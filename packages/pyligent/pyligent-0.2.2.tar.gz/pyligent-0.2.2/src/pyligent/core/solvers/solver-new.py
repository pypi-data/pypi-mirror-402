from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, override

import torch
from loguru import logger
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    LogitsProcessor,
    LogitsProcessorList,
    PreTrainedModel,
    StoppingCriteriaList,
    StopStringCriteria,
    get_cosine_schedule_with_warmup,
)

from pyligent.common.tensorboard_logger import (
    TensorBoardPerformanceLogger,
    TensorBoardPhaseLogger,
)
from pyligent.core import DiligentDataset, SamplingDatasetFunction, Solver
from pyligent.core.action import Action, DoneAction
from pyligent.core.path import PathContext


# ============================================================================
# Tokens config
# ============================================================================
@dataclass
class DiligentTokensConfig:
    """Configuration for special tokens used in action generation."""

    node_start: str = "<node>"
    node_end: str = "</node>"
    backtrack_start: str = "<backtrack>"
    backtrack_end: str = "</backtrack>"
    done_start: str = "<done>"
    done_end: str = "</done>"

    use_backtrack_in_inference: bool = False
    stopping_tokens: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stopping_tokens:
            self.stopping_tokens = [self.node_end, self.done_end]
            if self.use_backtrack_in_inference:
                self.stopping_tokens.append(self.backtrack_end)

    def get_all_special_tokens(self) -> list[str]:
        return [
            self.node_start,
            self.node_end,
            self.backtrack_start,
            self.backtrack_end,
            self.done_start,
            self.done_end,
        ]

    def get_inference_tags(self) -> list[str]:
        tags = [self.node_start, self.done_start]
        if self.use_backtrack_in_inference:
            tags.append(self.backtrack_start)
        return tags


# ============================================================================
# Helpers
# ============================================================================
def _set_torch_perf_flags() -> None:
    """Enable TF32 for faster matmul on Ampere+ GPUs."""
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True


def _supports_kw(fn, kw: str) -> bool:
    """Check if function supports a keyword argument."""
    try:
        import inspect

        return kw in inspect.signature(fn).parameters
    except Exception:
        return False


def _ctx_to_text(ctx: PathContext) -> str:
    """Convert PathContext to string representation."""
    return "\n".join(str(node.action) for node in ctx.nodes) if ctx else ""


class _ForceFirstGeneratedToken(LogitsProcessor):
    """
    Force the first newly generated token to be in `allowed_token_ids`.

    Keeps HF generation batched (fast K on one GPU) while ensuring output begins with a tag.
    """

    def __init__(self, *, prompt_len: int, allowed_token_ids: list[int]) -> None:
        self.prompt_len = int(prompt_len)
        self.allowed = {
            int(t) for t in allowed_token_ids if t is not None and int(t) >= 0
        }

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor
    ) -> torch.FloatTensor:
        if input_ids.shape[1] != self.prompt_len:
            return scores
        if not self.allowed:
            return scores

        mask = torch.full_like(scores, float("-inf"))
        for tid in self.allowed:
            mask[:, tid] = 0.0
        return scores + mask


# ============================================================================
# Training dataset
# ============================================================================
class _PairsDataset(Dataset):
    """Dataset that formats (PathContext, Action) pairs for supervised fine-tuning."""

    def __init__(
        self,
        pairs: list[tuple[PathContext, Action]],
        tokenizer,
        system_prompt: str,
        user_prompt: str,
        max_length: int,
        tokens_cfg: DiligentTokensConfig,
        chat_mode: Literal["user", "assistant"] = "assistant",
    ) -> None:
        self.pairs = pairs
        self.tokenizer = tokenizer
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.max_length = max_length
        self.tokens_cfg = tokens_cfg
        self.chat_mode = chat_mode

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def __len__(self) -> int:
        return len(self.pairs)

    def _render_chat(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
        continue_final_message: bool,
    ) -> str:
        fn = self.tokenizer.apply_chat_template
        kwargs: dict = {"tokenize": False}

        if _supports_kw(fn, "add_generation_prompt"):
            kwargs["add_generation_prompt"] = add_generation_prompt

        if continue_final_message and _supports_kw(fn, "continue_final_message"):
            kwargs["continue_final_message"] = True

        if _supports_kw(fn, "enable_thinking"):
            kwargs["enable_thinking"] = False

        return fn(messages, **kwargs)

    def _build_messages(
        self, ctx: PathContext, *, for_generation: bool
    ) -> tuple[list[dict[str, str]], bool, bool]:
        """
        Returns:
            (messages, add_generation_prompt, continue_final_message)
        """
        if self.chat_mode == "assistant" and ctx and len(ctx.nodes) >= 1:
            # assistant mode: user is first node text, assistant contains history
            user_content = str(ctx.nodes[0].action.text)
            assistant_history = (
                "\n".join(str(n.action) for n in ctx.nodes) if len(ctx.nodes) > 1 else ""
            )
            if assistant_history:
                assistant_history += "\n"

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_history},
            ]
            return messages, (not for_generation), True

        # user mode: user gets PATH
        ctx_text = _ctx_to_text(ctx)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt.format(ctx=ctx_text)},
        ]
        return messages, True, False

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        ctx, act = self.pairs[idx]

        messages, add_generation_prompt, continue_final_message = self._build_messages(
            ctx, for_generation=True
        )

        if continue_final_message and not _supports_kw(
            self.tokenizer.apply_chat_template, "continue_final_message"
        ):
            continue_final_message = False
            add_generation_prompt = True

        prompt_text = self._render_chat(
            messages,
            add_generation_prompt=add_generation_prompt,
            continue_final_message=continue_final_message,
        )
        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False).input_ids

        completion_text = str(act)
        completion_ids = self.tokenizer(
            completion_text, add_special_tokens=False
        ).input_ids

        if isinstance(act, DoneAction) and self.tokenizer.eos_token_id is not None:
            completion_ids = completion_ids + [self.tokenizer.eos_token_id]

        input_ids = prompt_ids + completion_ids
        labels = [-100] * len(prompt_ids) + completion_ids
        attention_mask = [1] * len(input_ids)

        if len(input_ids) > self.max_length:
            input_ids = input_ids[: self.max_length]
            labels = labels[: self.max_length]
            attention_mask = attention_mask[: self.max_length]

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def _collate_pad(
    tokenizer, batch: list[dict[str, torch.Tensor]]
) -> dict[str, torch.Tensor]:
    pad_id = (
        tokenizer.pad_token_id
        if tokenizer.pad_token_id is not None
        else tokenizer.eos_token_id
    )
    input_ids = torch.nn.utils.rnn.pad_sequence(
        [b["input_ids"] for b in batch], batch_first=True, padding_value=pad_id
    )
    attention_mask = torch.nn.utils.rnn.pad_sequence(
        [b["attention_mask"] for b in batch], batch_first=True, padding_value=0
    )
    labels = torch.nn.utils.rnn.pad_sequence(
        [b["labels"] for b in batch], batch_first=True, padding_value=-100
    )
    return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


# ============================================================================
# LlmSolver (single GPU, no accelerate)
# ============================================================================
class LlmSolver(Solver):
    """
    Single-GPU, accelerate-free LlmSolver.

    Training uses manual gradient accumulation and AMP with optional GradScaler. [web:31]
    """

    _DEFAULT_SYS = (
        "You are a diligent reasoning solver.\n"
        "Given the PATH context, output exactly ONE next action as a SINGLE XML-like tag:\n"
        "  <node>ID STEP_TEXT</node>\n"
        "  <backtrack>ID</backtrack>\n"
        "  <done>FINAL_ANSWER</done>\n\n"
        "Rules:\n"
        "- Output ONLY one tag and nothing else.\n"
        "- Use <done> only when the solution is finished.\n"
        "- Use <backtrack> only to jump to a previous node ID.\n"
    )
    _DEFAULT_USER = "PATH:\n{ctx}\n\nNext action?"

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        use_qlora: bool = True,
        bf16: bool = True,
        lr: float = 2e-5,
        max_seq_len: int = 2048,
        out_dir: Path = Path("output"),
        gen_cfg: Optional[dict] = None,
        checkpoint_save_steps: int = 200,
        checkpoint_save_total_limit: int = 5,
        chat_mode: Literal["user", "assistant"] = "assistant",
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        use_k_sequences: bool = True,
        train_batch_size: int = 1,
        grad_accum_steps: int = 8,
        warmup_ratio: float = 0.03,
        weight_decay: float = 0.01,
        max_grad_norm: float = 1.0,
        use_flash_attention_2: bool = False,
        use_guidance: bool = False,
        use_backtrack_in_inference: bool = False,
    ):
        super().__init__(out_dir)
        _set_torch_perf_flags()

        self.chat_mode = chat_mode
        self.system_prompt: str = system_prompt or self._DEFAULT_SYS
        self.user_prompt: str = user_prompt or self._DEFAULT_USER

        self.model_name = model_name
        self.use_qlora = use_qlora
        self.use_guidance = use_guidance

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # bf16 uses autocast without GradScaler; fp16 uses GradScaler for stability. [web:31]
        self.dtype = (
            torch.bfloat16 if (bf16 and torch.cuda.is_available()) else torch.float16
        )

        self.lr = lr
        self.max_seq_len = max_seq_len
        self.use_k_sequences = use_k_sequences

        self.train_batch_size = train_batch_size
        self.grad_accum_steps = max(1, int(grad_accum_steps))
        self.warmup_ratio = warmup_ratio
        self.weight_decay = weight_decay
        self.max_grad_norm = max_grad_norm
        self.checkpoint_save_steps = checkpoint_save_steps
        self.checkpoint_save_total_limit = checkpoint_save_total_limit

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, use_fast=True, padding_side="left"
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.tokens_cfg = DiligentTokensConfig(
            use_backtrack_in_inference=use_backtrack_in_inference
        )
        self.tokenizer.add_special_tokens(
            {"additional_special_tokens": self.tokens_cfg.get_all_special_tokens()}
        )

        logger.info(
            f"Loading model '{model_name}' (QLoRA={use_qlora}, dtype={self.dtype})"
        )
        quant_cfg = None
        device_map = "auto"
        if use_qlora and torch.cuda.is_available():
            quant_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            # single GPU placement
            device_map = {"": 0}

        attn_impl = (
            "flash_attention_2"
            if (use_flash_attention_2 and torch.cuda.is_available())
            else None
        )

        self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device_map,
            dtype=self.dtype,
            quantization_config=quant_cfg,
            attn_implementation=attn_impl,
        )
        self.model.resize_token_embeddings(len(self.tokenizer))
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        self.model.config.eos_token_id = self.tokenizer.eos_token_id

        if not (use_qlora and torch.cuda.is_available()):
            self.model.to(self.device)

        self._stopping_criteria = StoppingCriteriaList(
            [
                StopStringCriteria(
                    tokenizer=self.tokenizer, stop_strings=self.tokens_cfg.stopping_tokens
                )
            ]
        )

        self.lora_cfg = self._build_lora_config()
        self.gen_cfg = self._default_gen_cfg(gen_cfg)

        self.trainer_phase_callback = TensorBoardPhaseLogger(
            self.out_dir, self.time_stamp
        )
        self.trainer_performance_callback = TensorBoardPerformanceLogger(
            self.out_dir, self.time_stamp
        )

        self._guidance_lm = None

        try:
            logging.getLogger("transformers").setLevel(logging.WARNING)
        except Exception:
            pass

    @staticmethod
    def _build_lora_config() -> LoraConfig:
        return LoraConfig(
            r=32,
            lora_alpha=64,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        )

    @staticmethod
    def _default_gen_cfg(overrides: Optional[dict]) -> dict:
        cfg = dict(
            max_new_tokens=128,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            top_k=50,
            repetition_penalty=1.0,
        )
        if overrides:
            cfg.update(overrides)
        return cfg

    def _render_chat(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
        continue_final_message: bool,
    ) -> str:
        fn = self.tokenizer.apply_chat_template
        kwargs: dict = {"tokenize": False}

        if _supports_kw(fn, "add_generation_prompt"):
            kwargs["add_generation_prompt"] = add_generation_prompt
        if continue_final_message and _supports_kw(fn, "continue_final_message"):
            kwargs["continue_final_message"] = True
        if _supports_kw(fn, "enable_thinking"):
            kwargs["enable_thinking"] = False

        return fn(messages, **kwargs)

    def _build_messages(
        self, ctx: PathContext, *, for_generation: bool
    ) -> tuple[list[dict[str, str]], bool, bool]:
        if self.chat_mode == "assistant" and ctx and len(ctx.nodes) >= 1:
            user_content = str(ctx.nodes[0].action.text)
            assistant_history = (
                "\n".join(str(n.action) for n in ctx.nodes) if len(ctx.nodes) > 1 else ""
            )
            if assistant_history:
                assistant_history += "\n"
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_history},
            ]
            return messages, (not for_generation), True

        ctx_text = _ctx_to_text(ctx)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt.format(ctx=ctx_text)},
        ]
        return messages, True, False

    def _build_prompt(self, ctx: PathContext) -> str:
        messages, add_generation_prompt, continue_final_message = self._build_messages(
            ctx, for_generation=True
        )

        if continue_final_message and not _supports_kw(
            self.tokenizer.apply_chat_template, "continue_final_message"
        ):
            continue_final_message = False
            add_generation_prompt = True

        return self._render_chat(
            messages,
            add_generation_prompt=add_generation_prompt,
            continue_final_message=continue_final_message,
        )

    def _tag_start_token_ids(self) -> list[int]:
        allowed: list[int] = []
        unk = self.tokenizer.unk_token_id
        for tok in self.tokens_cfg.get_inference_tags():
            tid = self.tokenizer.convert_tokens_to_ids(tok)
            if tid is None:
                continue
            if unk is not None and tid == unk:
                logger.warning(
                    f"Special token {tok!r} maps to UNK; cannot hard-constrain start token for this tag."
                )
                continue
            allowed.append(int(tid))
        return allowed

    def finetune(
        self,
        dataset_sampling_function: SamplingDatasetFunction,
        epochs: int,
        t: int,
        eval_dataset: Optional[object] = None,
        phase: str = "SFT",
        **kwargs,
    ) -> None:
        self.trainer_phase_callback.set_phase(phase, t)

        self.model.train()
        self.model.config.use_cache = False
        if hasattr(self.model, "gradient_checkpointing_enable"):
            self.model.gradient_checkpointing_enable()

        if self.use_qlora:
            self.model = prepare_model_for_kbit_training(self.model)

        if not hasattr(self.model, "peft_config"):
            self.model = get_peft_model(self.model, self.lora_cfg)

        optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )

        # fp16 => GradScaler; bf16 => no scaler (recommended path). [web:31]
        use_scaler = torch.cuda.is_available() and self.dtype == torch.float16
        scaler = torch.cuda.amp.GradScaler(enabled=use_scaler)

        for epoch in range(epochs):
            diligent_ds: DiligentDataset = dataset_sampling_function()

            train_loader = DataLoader(
                _PairsDataset(
                    diligent_ds.pairs,
                    self.tokenizer,
                    self.system_prompt,
                    self.user_prompt,
                    self.max_seq_len,
                    self.tokens_cfg,
                    chat_mode=self.chat_mode,
                ),
                batch_size=self.train_batch_size,
                shuffle=True,
                collate_fn=lambda b: _collate_pad(self.tokenizer, b),
                num_workers=0,
                pin_memory=torch.cuda.is_available(),
            )

            # HF cosine warmup scheduler (same as before). [web:17]
            steps_per_epoch = max(1, (len(train_loader) // self.grad_accum_steps))
            lr_scheduler = get_cosine_schedule_with_warmup(
                optimizer,
                num_warmup_steps=int(steps_per_epoch * self.warmup_ratio),
                num_training_steps=steps_per_epoch,
            )

            logger.info(
                f"Epoch {epoch + 1}/{epochs}: training on {len(diligent_ds.pairs)} samples."
            )
            optimizer.zero_grad(set_to_none=True)

            step = 0
            for micro_i, batch in enumerate(train_loader):
                batch = {
                    k: v.to(self.device, non_blocking=True) for k, v in batch.items()
                }

                # Gradient accumulation pattern: divide loss by accum steps and step optimizer periodically. [web:31]
                with torch.cuda.amp.autocast(
                    enabled=torch.cuda.is_available(),
                    dtype=self.dtype if torch.cuda.is_available() else None,
                ):
                    out = self.model(**batch)
                    loss = out.loss / self.grad_accum_steps

                if use_scaler:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()

                is_update_step = (micro_i + 1) % self.grad_accum_steps == 0

                if is_update_step:
                    if use_scaler:
                        # Unscale before clipping, then clip, then step. [web:36][web:39]
                        scaler.unscale_(optimizer)

                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.max_grad_norm
                    )

                    if use_scaler:
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        optimizer.step()

                    lr_scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                    step += 1

                    if step % 10 == 0:
                        logger.info(
                            f"[e{epoch + 1}] step={step}/{steps_per_epoch} loss={out.loss.detach().float().item():.4f}"
                        )

                    if step % self.checkpoint_save_steps == 0:
                        self._save_checkpoint(epoch=epoch, step=step)

                    if step >= steps_per_epoch:
                        break

        logger.success("✓ Training completed.\n")

    def _save_checkpoint(self, *, epoch: int, step: int) -> None:
        ckpt_dir = self.out_dir / "checkpoints" / f"epoch-{epoch + 1}-step-{step}"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(ckpt_dir)
        self.tokenizer.save_pretrained(ckpt_dir)

    def propose_actions(
        self, contexts: list[PathContext], max_actions: int = 0
    ) -> tuple[list[list[Action | str]], int]:
        if not contexts:
            return ([], 0)

        K = max(1, int(max_actions) if max_actions else 1)

        if self.use_k_sequences:
            return self._propose_actions_k_sequences(contexts, K=K)
        return self._propose_actions_sequential(contexts, K=K)

    def _prepare_model_for_inference(self) -> None:
        self.model.eval()
        if hasattr(self.model, "gradient_checkpointing_disable"):
            self.model.gradient_checkpointing_disable()
        if hasattr(self.model.config, "use_cache"):
            self.model.config.use_cache = True

    def _prepare_batch_inputs(self, contexts: list[PathContext]) -> tuple[dict, int]:
        prompt_texts = [self._build_prompt(ctx) for ctx in contexts]
        inputs = self.tokenizer(prompt_texts, return_tensors="pt", padding=True).to(
            self.device
        )
        prompt_len = inputs["input_ids"].shape[1]
        return inputs, prompt_len

    def _decode_new_tokens(self, outputs: torch.Tensor, prompt_len: int) -> list[str]:
        new_tokens = outputs[:, prompt_len:]
        return self.tokenizer.batch_decode(new_tokens, skip_special_tokens=False)

    def _propose_actions_k_sequences(
        self, contexts: list[PathContext], K: int
    ) -> tuple[list[list[str]], int]:
        """Fast-K single GPU: one batched generate() using num_return_sequences=K."""
        self._prepare_model_for_inference()
        inputs, prompt_len = self._prepare_batch_inputs(contexts)

        gen_cfg = dict(self.gen_cfg)
        gen_cfg["num_beams"] = 1
        gen_cfg["num_return_sequences"] = K

        logits_processor = LogitsProcessorList(
            [
                _ForceFirstGeneratedToken(
                    prompt_len=prompt_len, allowed_token_ids=self._tag_start_token_ids()
                )
            ]
        )

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                **gen_cfg,
                stopping_criteria=self._stopping_criteria,
                logits_processor=logits_processor,
                tokenizer=self.tokenizer,
            )

        decoded = self._decode_new_tokens(outputs, prompt_len)
        N = len(contexts)
        batched_actions = [decoded[i * K : (i + 1) * K] for i in range(N)]

        del inputs, outputs
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return batched_actions, 1

    def _propose_actions_sequential(
        self, contexts: list[PathContext], K: int
    ) -> tuple[list[list[str]], int]:
        """Sequential K calls (lower peak mem); keeps same first-token constraint."""
        self._prepare_model_for_inference()
        inputs, prompt_len = self._prepare_batch_inputs(contexts)

        gen_cfg = dict(self.gen_cfg)
        gen_cfg["num_beams"] = 1
        gen_cfg["num_return_sequences"] = 1

        logits_processor = LogitsProcessorList(
            [
                _ForceFirstGeneratedToken(
                    prompt_len=prompt_len, allowed_token_ids=self._tag_start_token_ids()
                )
            ]
        )

        all_generated: list[list[str]] = []
        with torch.inference_mode():
            for k in range(K):
                outputs = self.model.generate(
                    **inputs,
                    **gen_cfg,
                    stopping_criteria=self._stopping_criteria,
                    logits_processor=logits_processor,
                    tokenizer=self.tokenizer,
                )
                all_generated.append(self._decode_new_tokens(outputs, prompt_len))
                del outputs
                if torch.cuda.is_available() and k < K - 1:
                    torch.cuda.empty_cache()

        N = len(contexts)
        batched_actions = [[all_generated[k][i] for k in range(K)] for i in range(N)]

        del inputs, all_generated
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return batched_actions, K

    @override
    def save(self, output_dir: Path, metadata: Optional[dict] = None) -> None:
        if self.model is None:
            raise RuntimeError("Solver model is None")
        output_dir.mkdir(parents=True, exist_ok=True)

        model_to_save = self.model
        if hasattr(model_to_save, "merge_and_unload"):
            try:
                model_to_save = model_to_save.merge_and_unload()
                logger.success("✓ LoRA merged for saving")
            except Exception as e:
                logger.warning(f"Failed to merge LoRA; saving adapter model. err={e}")

        model_to_save.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        meta = {
            "model_name": self.model_name,
            "use_qlora": self.use_qlora,
            "lr": self.lr,
            "gen_cfg": self.gen_cfg,
            "chat_mode": self.chat_mode,
            "use_backtrack_in_inference": self.tokens_cfg.use_backtrack_in_inference,
        }
        if metadata:
            meta.update(metadata)

        with open(output_dir / "training_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.success(f"✓ Checkpoint saved to {output_dir}")
