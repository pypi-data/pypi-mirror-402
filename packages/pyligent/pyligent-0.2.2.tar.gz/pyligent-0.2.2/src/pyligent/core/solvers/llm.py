import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional, override

import torch
import torch.distributed as dist
from datasets import Dataset
from datasets import Dataset as HFDataset
from datasets import IterableDataset as HFIterableDataset
from loguru import logger
from peft import LoraConfig, PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    StoppingCriteriaList,
    StopStringCriteria,
    TrainerCallback,
)
from trl.trainer.sft_config import SFTConfig
from trl.trainer.sft_trainer import SFTTrainer

from pyligent.common.tensorboard_logger import (
    TensorBoardPerformanceLogger,
    TensorBoardPhaseLogger,
)
from pyligent.core import Solver
from pyligent.core.action import Action
from pyligent.core.path import PathContext
from pyligent.core.solvers.llm_helpers import SolverParquetWriter

GeneralHFDataset = HFDataset | HFIterableDataset


def configure_iterable_training(
    *,
    train_ds: HFIterableDataset,
    sft_cfg: SFTConfig,
    epochs: int,
) -> None:
    """
    Configure SFTConfig for IterableDataset training:
    - Clamps gradient_accumulation_steps if dataset is too small
    - Computes and sets max_steps based on samples per epoch

    Modifies sft_cfg in-place.
    """
    # 1. Retrieve the sample count we tagged earlier
    samples_per_epoch = getattr(train_ds, "_pyligent_snapshot_n", None)
    if samples_per_epoch is None:
        raise ValueError(
            "IterableDataset training requires a known samples_per_epoch. "
            "Ensure sampling_strategy.max_samples is set."
        )
    samples_per_epoch = int(samples_per_epoch)

    # 2. Calculate actual batches per epoch
    try:
        world_size = (
            dist.get_world_size() if dist.is_available() and dist.is_initialized() else 1  # ty:ignore[possibly-missing-attribute]
        )
    except Exception:
        world_size = int(os.environ.get("WORLD_SIZE", "1"))

    per_device_bs = int(sft_cfg.per_device_train_batch_size)
    batches_per_epoch = math.ceil(samples_per_epoch / max(1, per_device_bs * world_size))

    # 3. CLAMP gradient_accumulation_steps
    #    If we have fewer batches than accum_steps, we must reduce accum_steps
    #    otherwise Trainer waits for multiple epochs just to do 1 step (causes hang).
    current_ga = int(sft_cfg.gradient_accumulation_steps)
    if batches_per_epoch < current_ga:
        new_ga = max(1, batches_per_epoch)
        logger.warning(
            f"Dataset too small ({samples_per_epoch} samples -> {batches_per_epoch} batches) "
            f"for grad_accum={current_ga}. Reducing gradient_accumulation_steps to {new_ga} "
            "to ensure training progress."
        )
        sft_cfg.gradient_accumulation_steps = new_ga
        current_ga = new_ga

    # 4. Compute max_steps with the SAFE gradient_accumulation_steps
    updates_per_epoch = math.ceil(batches_per_epoch / max(1, current_ga))
    sft_cfg.max_steps = int(epochs) * int(updates_per_epoch)

    # Ensure we perform at least 1 step if data exists
    if sft_cfg.max_steps == 0 and samples_per_epoch > 0:
        sft_cfg.max_steps = 1


# ==========================================================================
# Tokens config
# ==========================================================================
@dataclass
class DiligentTokensConfig:
    node_start: str = "<node>"
    node_end: str = "</node>"
    backtrack_start: str = "<backtrack>"
    backtrack_end: str = "</backtrack>"
    done_start: str = "<done>"
    done_end: str = "</done>"
    stopping_tokens: list[str] = field(default_factory=list)

    def __post_init__(self):
        if len(self.stopping_tokens) == 0:
            self.stopping_tokens = [self.node_end, self.backtrack_end, self.done_end]

    def get_all_special_tokens(self) -> list[str]:
        return [
            self.node_start,
            self.node_end,
            self.backtrack_start,
            self.backtrack_end,
            self.done_start,
            self.done_end,
        ]


# ==========================================================================
# Dtype utils
# ==========================================================================
def ensure_dtype_consistency(model: PreTrainedModel, target_dtype: torch.dtype):
    casted = []

    try:
        if hasattr(model, "get_input_embeddings"):
            emb = model.get_input_embeddings()
            if emb is not None:
                emb.to(target_dtype)
                casted.append("input_embeddings")
    except Exception:
        pass

    try:
        if hasattr(model, "get_output_embeddings"):
            oemb = model.get_output_embeddings()
            if oemb is not None:
                oemb.to(target_dtype)
                casted.append("output_embeddings")
    except Exception:
        pass

    roots = [
        (model, "model"),
        (getattr(model, "base_model", None), "base_model"),
        (getattr(getattr(model, "base_model", None), "model", None), "base_model.model"),
    ]

    for root, rname in roots:
        if root is None:
            continue
        try:
            lm = getattr(root, "lm_head", None)
            if lm is not None:
                lm.to(target_dtype)
                casted.append(f"{rname}.lm_head")
        except Exception:
            pass


def _register_lm_head_input_cast_hook(
    linear_module: torch.nn.Module,
) -> torch.utils.hooks.RemovableHandle:
    def _pre_hook(mod, inputs):
        if not inputs:
            return inputs
        x = inputs[0]
        if isinstance(x, torch.Tensor):
            tgt = mod.weight.dtype
            if x.dtype != tgt:
                x = x.to(tgt)
                return (x,) + inputs[1:]
        return inputs

    return linear_module.register_forward_pre_hook(_pre_hook)


def apply_lm_head_cast_hooks(
    model: PreTrainedModel,
) -> list[torch.utils.hooks.RemovableHandle]:
    hooks: list[torch.utils.hooks.RemovableHandle] = []
    seen: list[torch.nn.Module] = []

    roots = [
        model,
        getattr(model, "base_model", None),
        getattr(getattr(model, "base_model", None), "model", None),
    ]

    for root in roots:
        if root is None:
            continue
        try:
            lm = getattr(root, "lm_head", None)
            if isinstance(lm, torch.nn.Linear) and lm not in seen:
                hooks.append(_register_lm_head_input_cast_hook(lm))
                seen.append(lm)
        except Exception:
            pass

    return hooks


class _SetEpochOnDatasetCallback(TrainerCallback):
    """Ensures IterableDataset shuffles advance per epoch by calling set_epoch()."""

    def on_epoch_begin(self, args, state, control, **kwargs):
        train_dataloader = kwargs.get("train_dataloader", None)
        if train_dataloader is None:
            return control

        ds = getattr(train_dataloader, "dataset", None)
        if ds is None:
            return control

        # state.epoch can be float; normalize to int.
        epoch_idx = int(state.epoch or 0)

        # Some wrappers (accelerate / transformers) wrap the dataset; try the common places.
        if hasattr(ds, "set_epoch"):
            ds.set_epoch(epoch_idx)
        elif hasattr(ds, "dataset") and hasattr(ds.dataset, "set_epoch"):
            ds.dataset.set_epoch(epoch_idx)

        return control


def _pyligent_row_to_text(
    row: dict,
    *,
    chat_mode: str,
    system_prompt: str,
    user_prompt: str,
    tokenizer,
) -> dict:
    # NOTE: tokenizer is passed in via fn_kwargs.

    parts = []
    if row.get("input"):
        parts.append(row["input"])
    parts.extend(row.get("prefix") or [])
    parts.extend(row.get("generated") or [])
    ctx_text = "\n".join(parts)

    target = row["final"]

    if chat_mode == "user":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.format(ctx=ctx_text)},
            {"role": "assistant", "content": target},
        ]
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
        )
    elif chat_mode == "assistant":
        assistant_content = "\n".join(
            (row.get("prefix") or []) + (row.get("generated") or [])
        )
        assistant_content = (
            assistant_content + f"\n{target}" if assistant_content else target
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (row.get("input") or "")},
            {"role": "assistant", "content": assistant_content},
        ]
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            enable_thinking=False,
            continue_final_message=False,
        )
    else:
        raise RuntimeError(f"Unknown chat mode `{chat_mode}`!")

    return {"text": prompt_text}


# ==========================================================================
# LlmSolver
# ==========================================================================
class LlmSolver(Solver):
    _DEFAULT_SYS = (
        "You must output exactly ONE next action using one of these forms:\n"
        " <node>ID STEP_TEXT</node>\n"
        " <done>FINAL_ANSWER</done>\n\n"
        "Never emit <backtrack>; backtracking is handled separately.\n"
        "Emit ONLY the tag. No commentary or reasoning."
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
        checkpoint_save_strategy: str = "steps",
        checkpoint_save_steps: int = 100,
        checkpoint_save_total_limit: int = 5,
        chat_mode: Literal["user", "assistant"] = "user",
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        use_k_sequences: bool = True,
    ):
        super().__init__(out_dir)
        self.chat_mode = chat_mode
        self.system_prompt: str = system_prompt or self._DEFAULT_SYS
        self.user_prompt: str = user_prompt or self._DEFAULT_USER
        self.model_name = model_name
        self.use_qlora = use_qlora
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = (
            torch.bfloat16 if bf16 and torch.cuda.is_available() else torch.float16
        )

        self.lr = lr
        self.bf16 = bf16
        self.use_k_sequences = use_k_sequences

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, use_fast=True, padding_side="left"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info(f"Set pad_token to eos_token: {self.tokenizer.eos_token}")

        if self.tokenizer.bos_token is None:
            logger.info(f"{self.model_name} model has no BOS token (this is expected)")

        logger.info(f"Loading model '{model_name}' with QLoRA={use_qlora}, BF16={bf16}")
        quant_cfg = None
        device_map = "auto"

        if use_qlora and torch.cuda.is_available():
            quant_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            device_map = {"": torch.cuda.current_device()}

        self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device_map,
            dtype=self.dtype,
            quantization_config=quant_cfg,
        )

        ensure_dtype_consistency(self.model, self.dtype)
        self._lm_head_hooks = apply_lm_head_cast_hooks(self.model)

        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        self.model.config.eos_token_id = self.tokenizer.eos_token_id
        self.model.config.bos_token_id = self.tokenizer.bos_token_id

        if (
            hasattr(self.model, "generation_config")
            and self.model.generation_config is not None
        ):
            gen_conf = self.model.generation_config
            gen_conf.pad_token_id = self.tokenizer.pad_token_id
            gen_conf.bos_token_id = self.tokenizer.bos_token_id

        config = DiligentTokensConfig()
        self._stopping_criteria = StoppingCriteriaList(
            [
                StopStringCriteria(
                    tokenizer=self.tokenizer, stop_strings=config.stopping_tokens
                )
            ]
        )

        self.lora_cfg = self._build_lora_config()
        self.sft_cfg = self._build_sft_config(
            self.out_dir,
            lr,
            max_seq_len,
            self.time_stamp,
            bf16,
            checkpoint_save_steps,
            checkpoint_save_strategy,
            checkpoint_save_total_limit,
        )
        self.gen_cfg = self._default_gen_cfg(gen_cfg)
        self.trainer: Optional[SFTTrainer] = None
        self.trainer_phase_callback = TensorBoardPhaseLogger(
            self.out_dir, self.time_stamp
        )
        self.trainer_performance_callback = TensorBoardPerformanceLogger(
            self.out_dir, self.time_stamp
        )

        # Centralized parquet writer (snapshots + proposed_actions)
        self._parquet_writer = SolverParquetWriter(self.out_dir)
        self._propose_actions_call_idx: int = 0

        logger.info("✓ LlmSolver initialized successfully.\n")

        try:
            logging.getLogger("trl").setLevel(logging.WARNING)
            logging.getLogger("transformers").setLevel(logging.WARNING)
        except Exception:
            pass

    @staticmethod
    def _build_lora_config() -> LoraConfig:
        return LoraConfig(
            r=16,
            lora_alpha=32,
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
    def _build_sft_config(
        out_dir: Path,
        lr: float,
        max_seq_len: int,
        time_stamp: str,
        bf16: bool = True,
        save_steps: int = 100,
        save_strategy: str = "steps",
        save_total_limit: int = 5,
    ) -> SFTConfig:
        return SFTConfig(
            output_dir=str(out_dir / "checkpoints"),
            logging_dir=str(out_dir / "tensorboard_logs" / time_stamp),
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=lr,
            logging_steps=10,
            save_steps=save_steps,
            save_strategy=save_strategy,
            save_total_limit=save_total_limit,
            warmup_ratio=0.03,
            bf16=bf16 and torch.cuda.is_available(),
            fp16=False,
            max_length=max_seq_len,
            packing=False,
            completion_only_loss=True,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
            lr_scheduler_type="cosine",
            weight_decay=0.01,
            dataloader_num_workers=0,
            remove_unused_columns=False,
            report_to=["tensorboard"],
        )

    @staticmethod
    def _default_gen_cfg(overrides: Optional[dict]) -> dict:
        cfg = dict(
            max_new_tokens=256,
            min_new_tokens=3,
            do_sample=True,
            top_p=0.8,
            temperature=0.7,
            top_k=20,
            min_p=0.0,
            repetition_penalty=1.0,
        )
        if overrides:
            cfg.update(overrides)
        return cfg

    def _ctx_text(self, ctx: PathContext) -> str:
        return "\n".join(str(node.action) for node in ctx.nodes) if ctx else ""

    def _ctx_text_from_row(self, row: dict) -> str:
        parts = []
        if row.get("input"):
            parts.append(row["input"])
        parts.extend(row.get("prefix") or [])
        parts.extend(row.get("generated") or [])
        return "\n".join(parts)

    def _stage_slug(self, phase: str) -> str:
        p = phase.strip().lower()
        if p == "sft-a":
            return "sft-a"
        if p == "sft-b":
            return "sft-b"
        if p == "final":
            return "final"
        return p.replace(" ", "-")

    def _rows_to_text(
        self,
        hf_rows: GeneralHFDataset,
        *,
        phase: str,
        t: int,
    ) -> GeneralHFDataset:
        """
        One implementation for both map-style Dataset and streaming IterableDataset.

        For IterableDataset, `.map()` is applied on-the-fly when iterating (no full materialization).
        """

        # Works for both Dataset and IterableDataset
        out = hf_rows.map(
            _pyligent_row_to_text,
            fn_kwargs={
                "chat_mode": self.chat_mode,
                "system_prompt": self.system_prompt,
                "user_prompt": self.user_prompt,
                "tokenizer": self.tokenizer,
            },
            remove_columns=list(hf_rows.column_names),  # ty:ignore[invalid-argument-type]
        )

        snap_n = getattr(hf_rows, "_pyligent_snapshot_n", None)
        if snap_n is not None:
            out._pyligent_snapshot_n = int(snap_n)  # ty:ignore[invalid-assignment]

        # Snapshot persistence: only do it for map-style datasets (avoid forcing full iteration).
        if isinstance(out, HFDataset):
            self._parquet_writer.write_finetunning_snapshot(
                out, stage=self._stage_slug(phase), t=t
            )
        elif isinstance(out, HFIterableDataset):
            snapshot_n = getattr(out, "_pyligent_snapshot_n", None)
            if snapshot_n is not None:
                snapshot_n = int(snapshot_n)
                if snapshot_n > 0:
                    rows = list(out.take(snapshot_n))
                    snap_ds = HFDataset.from_list(rows)
                    self._parquet_writer.write_finetunning_snapshot(
                        snap_ds, stage=self._stage_slug(phase), t=t
                    )

        return out

    def finetune(
        self,
        dataset: GeneralHFDataset,
        epochs: int,
        t: int,
        eval_dataset: Optional[Dataset] = None,
        phase: str = "SFT-A",
        **kwargs,
    ):
        """Finetune with dataset materialized once (no per-epoch resampling)."""
        self.trainer_phase_callback.set_phase(phase, t)

        train_ds = self._rows_to_text(dataset, phase=phase, t=t)

        if isinstance(train_ds, HFDataset):
            self.sft_cfg.num_train_epochs = epochs  # for Dataset

        if isinstance(train_ds, HFIterableDataset):
            configure_iterable_training(
                train_ds=train_ds, sft_cfg=self.sft_cfg, epochs=epochs
            )

        trainer_kwargs = dict(
            model=self.model,
            processing_class=self.tokenizer,
            args=self.sft_cfg,
            train_dataset=train_ds,
            eval_dataset=eval_dataset,
        )

        if not isinstance(self.model, PeftModel):
            trainer_kwargs["peft_config"] = self.lora_cfg

        self.trainer = SFTTrainer(**trainer_kwargs)  # ty:ignore[invalid-argument-type]
        ensure_dtype_consistency(self.trainer.model, self.dtype)  # ty:ignore[invalid-argument-type]

        self.trainer.add_callback(self.trainer_phase_callback)
        self.trainer.add_callback(self.trainer_performance_callback)
        self.trainer.add_callback(_SetEpochOnDatasetCallback())

        self.trainer.train()
        self.trainer.accelerator.wait_for_everyone()

        self.model = self.trainer.model  # type: ignore
        ensure_dtype_consistency(self.model, self.dtype)
        self._lm_head_hooks = apply_lm_head_cast_hooks(self.model)

        logger.success("✓ Training completed!\n")

    def propose_actions(
        self,
        *,
        contexts: list[PathContext],
        t: int,
        max_actions: int = 1,
    ) -> tuple[list[list[Action | str]], int]:
        """
        `t` is required; raw LLM inputs/outputs are persisted to parquet.
        """
        if self.use_k_sequences:
            return self._propose_actions_k_sequences(
                contexts, t=t, max_actions=max_actions
            )
        return self._propose_actions_1_sequence_loop(
            contexts, t=t, max_actions=max_actions
        )

    def _prepare_inputs(self, contexts: list[PathContext]):
        # model inference toggles
        self.model.eval()
        if hasattr(self.model, "gradient_checkpointing_disable"):
            self.model.gradient_checkpointing_disable()
        if hasattr(self.model.config, "use_cache"):
            self.model.config.use_cache = True

        if not contexts:
            return None, []

        prompt_texts = []
        for ctx in contexts:
            ctx_text = self._ctx_text(ctx)

            if self.chat_mode == "user":
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.user_prompt.format(ctx=ctx_text)},
                ]
                prompt_text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
            elif self.chat_mode == "assistant":
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": str(ctx[0].action)},
                    {
                        "role": "assistant",
                        "content": "\n".join(str(node.action) for node in ctx.nodes[1:])
                        if ctx
                        else "",
                    },
                ]
                prompt_text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    enable_thinking=False,
                    continue_final_message=True,
                )
            else:
                raise RuntimeError(f"Unknown chat mode `{self.chat_mode}`!")

            prompt_texts.append(prompt_text)

        device = next(self.model.parameters()).device
        inputs = self.tokenizer(prompt_texts, return_tensors="pt", padding=True).to(
            device
        )
        return inputs, prompt_texts

    def _sampling_gen_cfg(self, K: int) -> dict:
        gen_cfg = dict(self.gen_cfg)
        gen_cfg.pop("num_return_sequences", None)

        gen_cfg["do_sample"] = True
        gen_cfg.setdefault("temperature", 0.8)
        gen_cfg.setdefault("top_p", 0.9)
        gen_cfg.setdefault("top_k", 50)
        gen_cfg["num_beams"] = 1
        gen_cfg["num_return_sequences"] = K
        return gen_cfg

    def _persist_propose_actions(
        self,
        *,
        contexts: list[PathContext],
        t: int,
        prompt_texts: list[str],
        K: int,
        completion_at: Callable[[int, int], str],
    ) -> None:
        """
        Single DRY sink for propose_actions parquet persistence.
        Expects callables to fetch (completion, completion_raw) for (ctx_idx, sample_idx).
        """
        call_id = self._propose_actions_call_idx
        self._propose_actions_call_idx += 1

        rows: list[dict[str, object]] = []
        for ctx_idx, ctx in enumerate(contexts):
            ctx_text = self._ctx_text(ctx)
            for sample_idx in range(K):
                rows.append(
                    {
                        "ctx_text": ctx_text,
                        "prompt_text": prompt_texts[ctx_idx],
                        "completion_text": completion_at(ctx_idx, sample_idx),
                    }
                )

        self._parquet_writer.write_inference_snapshot(
            rows, t=int(t), call_id=int(call_id)
        )

    def _propose_actions_k_sequences(
        self, contexts: list[PathContext], *, t: int, max_actions: int = 0
    ) -> tuple[list[list[Action | str]], int]:
        """Single call: num_return_sequences=K (fast, higher peak memory)."""
        solver_calls = 0
        inputs, prompt_texts = self._prepare_inputs(contexts)
        if inputs is None:
            return ([], solver_calls)

        K = max(1, int(max_actions) if max_actions else 1)
        gen_cfg = self._sampling_gen_cfg(K=K)
        prompt_len = inputs["input_ids"].shape[1]

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                **gen_cfg,
                stopping_criteria=self._stopping_criteria,
                tokenizer=self.tokenizer,
            )  # ty:ignore[call-non-callable]
            solver_calls += 1

        new_tokens = outputs[:, prompt_len:]
        decoded_clean = self.tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
        self.tokenizer.batch_decode(new_tokens, skip_special_tokens=False)

        N = len(contexts)
        batched_actions: list[list[Action | str]] = [
            decoded_clean[i * K : (i + 1) * K] for i in range(N)
        ]

        def _at(ctx_idx: int, sample_idx: int) -> str:
            return decoded_clean[ctx_idx * K + sample_idx]

        self._persist_propose_actions(
            contexts=contexts,
            t=t,
            prompt_texts=prompt_texts,
            K=K,
            completion_at=_at,
        )

        del inputs, outputs, new_tokens
        torch.cuda.empty_cache()
        return (batched_actions, solver_calls)

    def _propose_actions_1_sequence_loop(
        self, contexts: list[PathContext], *, t: int, max_actions: int = 0
    ) -> tuple[list[list[Action | str]], int]:
        """K calls: num_return_sequences=1 (lower peak memory, slower)."""
        solver_calls = 0
        inputs, prompt_texts = self._prepare_inputs(contexts)
        if inputs is None:
            return ([], solver_calls)

        K = max(1, int(max_actions) if max_actions else 1)
        gen_cfg = self._sampling_gen_cfg(K=1)
        prompt_len = inputs["input_ids"].shape[1]

        all_generated_clean: list[list[str]] = []
        all_generated_raw: list[list[str]] = []

        with torch.inference_mode():
            for k in range(K):
                outputs = self.model.generate(
                    **inputs,
                    **gen_cfg,
                    stopping_criteria=self._stopping_criteria,
                    tokenizer=self.tokenizer,
                )  # ty:ignore[call-non-callable]
                solver_calls += 1

                new_tokens = outputs[:, prompt_len:]
                all_generated_clean.append(
                    self.tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
                )
                all_generated_raw.append(
                    self.tokenizer.batch_decode(new_tokens, skip_special_tokens=False)
                )

                del outputs, new_tokens
                if k < K - 1:
                    torch.cuda.empty_cache()

        N = len(contexts)
        batched_actions: list[list[Action | str]] = [
            [all_generated_clean[k][i] for k in range(K)] for i in range(N)
        ]

        def _at(ctx_idx: int, sample_idx: int) -> str:
            return all_generated_clean[sample_idx][ctx_idx]  # noqa: F821

        self._persist_propose_actions(
            contexts=contexts,
            t=t,
            prompt_texts=prompt_texts,
            K=K,
            completion_at=_at,
        )

        del inputs, all_generated_clean, all_generated_raw
        torch.cuda.empty_cache()
        return (batched_actions, solver_calls)

    @override
    def save(self, output_dir: Path, metadata: Optional[dict] = None):
        if self.model is None:
            logger.error("Solver model is None")
            raise RuntimeError("Solver model is None")

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving model checkpoint to {output_dir}...")

        if hasattr(self.model, "merge_and_unload"):
            merged_model = self.model.merge_and_unload()  # type: ignore
            merged_model.save_pretrained(output_dir)
            logger.success("✓ Model saved (LoRA merged)")
        else:
            self.model.save_pretrained(output_dir)
            logger.success("✓ Model saved")

        self.tokenizer.save_pretrained(output_dir)
        logger.success("✓ Tokenizer saved")

        training_metadata = {
            "model_name": self.model_name,
            "use_qlora": self.use_qlora,
            "bf16": self.bf16,
            "lr": self.lr,
            "gen_cfg": self.gen_cfg,
        }

        if metadata:
            training_metadata.update(metadata)
        metadata_file = output_dir / "training_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.success(f"✓ Metadata saved to {metadata_file}")

        logger.success(f"✓ Complete checkpoint saved to {output_dir}")
