"""
Abstract evaluator interface for consistent evaluation across datasets.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import torch
from loguru import logger
from peft import AutoPeftModelForCausalLM
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    StoppingCriteriaList,
    StopStringCriteria,
)

from pyligent.core.action import Action, BacktrackAction, NodeAction


@dataclass
class EvaluationConfig:
    """Configuration for evaluation runs."""

    # Model config
    checkpoint_path: str
    is_peft_adapter: Optional[bool] = None  # Auto-detect if None
    device_map: str = "auto"
    dtype: str = "bfloat16"

    # Generation config
    generation: dict[str, Any] = field(default_factory=dict)

    # Prompt config
    prompt: dict[str, Any] = field(default_factory=dict)

    # Token config
    tokens: dict[str, Any] = field(default_factory=dict)

    # Evaluation config
    evaluation: dict[str, Any] = field(default_factory=dict)

    # Logging config
    logging: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> EvaluationConfig:
        """Create config from dictionary (loaded from YAML)."""
        return cls(
            checkpoint_path=config["model"]["checkpoint_path"],
            is_peft_adapter=config["model"].get("is_peft_adapter"),
            device_map=config["model"].get("device_map", "auto"),
            dtype=config["model"].get("dtype", "bfloat16"),
            generation=config.get("generation", {}),
            prompt=config.get("prompt", {}),
            tokens=config.get("tokens", {}),
            evaluation=config.get("evaluation", {}),
            logging=config.get("logging", {}),
        )


@dataclass
class EvaluationResult:
    """Result of evaluating a single example."""

    question: str
    expected: str
    predicted: Optional[str]
    steps: list[str]
    correct: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question": self.question,
            "expected": self.expected,
            "predicted": self.predicted,
            "steps": self.steps,
            "correct": self.correct,
            "metadata": self.metadata,
        }


class BaseEvaluator(ABC):
    """
    Abstract base class for dataset evaluators.

    Handles model loading, inference, and result aggregation.
    Subclasses implement dataset-specific logic.
    """

    def __init__(self, config: EvaluationConfig):
        """Initialize evaluator with configuration."""
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model and tokenizer
        self.model: Any
        self.model, self.tokenizer = self._load_model_and_tokenizer()

        # Setup stopping criteria
        self.stopping_criteria = self._build_stopping_criteria()

        logger.info("✓ Evaluator initialized successfully")

    def _get_dtype(self) -> torch.dtype:
        """Convert dtype string to torch dtype."""
        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        return dtype_map.get(self.config.dtype, torch.bfloat16)

    def _load_model_and_tokenizer(self) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
        """Load model and tokenizer from checkpoint."""
        checkpoint_dir = Path(self.config.checkpoint_path)
        adapter_config_path = checkpoint_dir / "adapter_config.json"

        # Auto-detect PEFT adapter if not specified
        is_peft = (
            self.config.is_peft_adapter
            if self.config.is_peft_adapter is not None
            else adapter_config_path.exists()
        )

        logger.info(
            f"Loading {'PEFT adapter' if is_peft else 'full model'} from {checkpoint_dir}"
        )

        if is_peft:
            model = AutoPeftModelForCausalLM.from_pretrained(
                str(checkpoint_dir),
                device_map=self.config.device_map,
                dtype=self._get_dtype(),
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                str(checkpoint_dir),
                device_map=self.config.device_map,
                dtype=self._get_dtype(),
            )

        tokenizer = AutoTokenizer.from_pretrained(
            str(checkpoint_dir), use_fast=True, fix_mistral_regex=True
        )

        # Configure padding and special tokens
        if model.config.pad_token_id is None and tokenizer.pad_token_id is not None:
            model.config.pad_token_id = tokenizer.pad_token_id
        model.config.eos_token_id = tokenizer.eos_token_id

        model.eval()
        if hasattr(model.config, "use_cache"):
            model.config.use_cache = True

        return model, tokenizer

    def _build_stopping_criteria(self) -> StoppingCriteriaList:
        """Build stopping criteria from token config."""
        tokens_cfg = self.config.tokens

        # Default stopping tokens if not specified
        stopping_tokens = tokens_cfg.get("stopping_tokens", [])
        if not stopping_tokens:
            stopping_tokens = [
                tokens_cfg.get("node_end", "</node>"),
                tokens_cfg.get("backtrack_end", "</backtrack>"),
                tokens_cfg.get("done_end", "</done>"),
            ]

        return StoppingCriteriaList(
            [StopStringCriteria(tokenizer=self.tokenizer, stop_strings=stopping_tokens)]
        )

    def _build_messages(self, path_text: str) -> list[dict[str, str]]:
        """Build chat messages from path text using prompt config."""
        prompt_cfg = self.config.prompt

        instruction = prompt_cfg.get("instruction", "")
        user_template = prompt_cfg.get(
            "user_template", "PATH:\n{path_text}\n\nNext action:"
        )

        system_role = prompt_cfg.get("system_role", "system")
        user_role = prompt_cfg.get("user_role", "user")

        return [
            {"role": system_role, "content": instruction},
            {"role": user_role, "content": user_template.format(path_text=path_text)},
        ]

    def _generate_step(self, path_text: str) -> str:
        """Generate a single step given current path."""
        messages = self._build_messages(path_text)

        # Apply chat template
        prompt_cfg = self.config.prompt
        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=prompt_cfg.get("add_generation_prompt", True),
            enable_thinking=prompt_cfg.get("enable_thinking", False),
        )

        # Tokenize and generate
        inputs = self.tokenizer(str(prompt_text), return_tensors="pt").to(self.device)

        gen_cfg = self.config.generation
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=gen_cfg.get("max_new_tokens", 256),
                min_new_tokens=gen_cfg.get("min_new_tokens", 3),
                do_sample=gen_cfg.get("do_sample", True),
                top_p=gen_cfg.get("top_p", 0.8),
                temperature=gen_cfg.get("temperature", 0.7),
                top_k=gen_cfg.get("top_k", 20),
                min_p=gen_cfg.get("min_p", 0.0),
                repetition_penalty=gen_cfg.get("repetition_penalty", 1.0),
                pad_token_id=self.tokenizer.pad_token_id,
                stopping_criteria=self.stopping_criteria,
            )

        # Decode only generated tokens
        gen_only = outputs[:, inputs["input_ids"].shape[1] :]  # type: ignore
        text = self.tokenizer.batch_decode(gen_only, skip_special_tokens=True)[0]

        return text

    @abstractmethod
    def load_dataset(self) -> list[dict[str, Any]]:
        """
        Load and prepare evaluation dataset.

        Returns:
            list of examples with 'question' and 'expected' keys
        """
        pass

    @abstractmethod
    def parse_action(self, text: str) -> Optional[Any]:
        """
        Parse generated text into an action.

        Args:
            text: Generated text from model

        Returns:
            Parsed action or None if parsing fails
        """
        pass

    @abstractmethod
    def extract_answer(self, action: Any) -> Optional[str]:
        """
        Extract final answer from action.

        Args:
            action: Parsed action

        Returns:
            Final answer string or None
        """
        pass

    @abstractmethod
    def compare_answers(self, predicted: str, expected: str) -> bool:
        """
        Compare predicted and expected answers.

        Args:
            predicted: Model's predicted answer
            expected: Ground truth answer

        Returns:
            True if answers match, False otherwise
        """
        pass

    def is_backtrack_action(self, action: Action) -> bool:
        """
        Check if action is a backtrack action.

        Args:
            action: Parsed action

        Returns:
            True if action is backtrack, False otherwise
        """
        return isinstance(action, BacktrackAction)

    def get_backtrack_target_id(self, action: Action) -> Optional[int]:
        """
        Extract target node ID from backtrack action.

        Args:
            action: Backtrack action

        Returns:
            Target node ID or None
        """
        if isinstance(action, BacktrackAction):
            return action.target_id
        return None

    def get_node_id(self, action: Action) -> Optional[int]:
        """
        Extract node ID from node action.

        Args:
            action: Node action

        Returns:
            Node ID or None
        """
        if isinstance(action, NodeAction):
            return action.node_id
        return None

    def evaluate_single(self, example: dict[str, Any]) -> EvaluationResult:
        """
        Evaluate a single example.

        Args:
            example: dict with 'question' and 'expected' keys

        Returns:
            EvaluationResult with prediction and correctness
        """
        question = example["question"]
        expected = example["expected"]

        eval_cfg = self.config.evaluation
        max_steps = eval_cfg.get("max_steps", 20)
        backtrack_mode = eval_cfg.get("backtrack_mode", "reset")

        # Initialize path with question node
        tokens_cfg = self.config.tokens
        node_start = tokens_cfg.get("node_start", "<node>")
        node_end = tokens_cfg.get("node_end", "</node>")

        initial_node = f"{node_start}0 {question} {node_end}"
        path_nodes = [initial_node]
        steps_emitted = []
        final_answer = None

        # Track node IDs for backtracking (only needed in reset mode)
        # Maps node_id -> index in path_nodes
        node_id_to_index: dict[int, int] = {0: 0}

        # Iterative generation loop
        for _step in range(max_steps):
            path_text = "\n".join(path_nodes)

            # Generate next step
            text = self._generate_step(path_text)
            action = self.parse_action(text)

            if action is None:
                # Failed to parse - stop
                break

            # Record step
            step_str = str(action)
            steps_emitted.append(step_str)

            # Check if done
            answer = self.extract_answer(action)
            if answer is not None:
                final_answer = answer
                break

            # Handle backtrack action
            if self.is_backtrack_action(action):
                if backtrack_mode == "reset":
                    # Setting 2: Reset context to backtracked node
                    target_id = self.get_backtrack_target_id(action)

                    if target_id is not None and target_id in node_id_to_index:
                        # Find the index of the target node
                        target_index = node_id_to_index[target_id]

                        # Truncate path to target node (inclusive)
                        path_nodes = path_nodes[: target_index + 1]

                        # Update node_id_to_index to remove truncated nodes
                        node_id_to_index = {
                            nid: idx
                            for nid, idx in node_id_to_index.items()
                            if idx <= target_index
                        }
                    else:
                        # Invalid backtrack target - log warning and continue
                        logger.warning(
                            f"Invalid backtrack target: {target_id}. "
                            f"Valid nodes: {list(node_id_to_index.keys())}"
                        )
                elif backtrack_mode == "preserve":
                    # Setting 1: Keep full context, just record the backtrack
                    # Backtrack action is already in steps_emitted, no context change
                    pass
                else:
                    raise ValueError(
                        f"Invalid backtrack_mode: {backtrack_mode}. "
                        f"Must be 'preserve' or 'reset'"
                    )
            else:
                # Regular node action - add to path
                path_nodes.append(step_str)

                # Track node ID for future backtracking
                node_id = self.get_node_id(action)
                if node_id is not None:
                    node_id_to_index[node_id] = len(path_nodes) - 1

        # Evaluate correctness
        is_correct = False
        if final_answer and expected:
            is_correct = self.compare_answers(final_answer, expected)

        return EvaluationResult(
            question=question,
            expected=expected,
            predicted=final_answer,
            steps=steps_emitted,
            correct=is_correct,
            metadata={
                "num_steps": len(steps_emitted),
                "backtrack_mode": backtrack_mode,
                "final_context_length": len(path_nodes),
            },
        )

    def evaluate(self) -> dict[str, Any]:
        """
        Run full evaluation on dataset.

        Returns:
            Dictionary with summary statistics and results
        """
        eval_cfg = self.config.evaluation

        # Load dataset
        logger.info("Loading dataset...")
        examples = self.load_dataset()

        # Limit examples if specified
        max_examples = eval_cfg.get("max_examples")
        if max_examples:
            examples = examples[:max_examples]

        logger.info(f"Evaluating {len(examples)} examples...")

        # Evaluate each example
        results = []
        correct_count = 0

        show_first = eval_cfg.get("show_first", 0)

        for i, example in enumerate(examples):
            result = self.evaluate_single(example)
            results.append(result)

            if result.correct:
                correct_count += 1

            # Print detailed output for first N examples
            if i < show_first:
                logger.log("TITLE", f"Example {i + 1}/{len(examples)}")

                logger.info(f"Question: {result.question}")
                logger.info(f"Expected: {result.expected}")
                logger.info(f"Steps: {result.steps}")
                logger.info(f"Predicted: {result.predicted}")
                logger.info(f"Correct: {result.correct}")

            # Progress logging
            if (i + 1) % 10 == 0:
                logger.info(
                    f"Progress: {i + 1}/{len(examples)} ({correct_count}/{i + 1} correct)"
                )

        # Compute summary statistics
        total = len(results)
        accuracy = correct_count / total if total > 0 else 0.0

        summary = {
            "total": total,
            "correct": correct_count,
            "accuracy": accuracy,
            "config": {
                "checkpoint": self.config.checkpoint_path,
                "max_steps": eval_cfg.get("max_steps"),
                "temperature": self.config.generation.get("temperature"),
            },
        }

        logger.log("SECTION", "EVALUATION SUMMARY")
        logger.info(f"Total examples: {total}")
        logger.info(f"Correct: {correct_count}")
        logger.info(f"Accuracy: {accuracy:.2%}")

        return {
            "summary": summary,
            "results": [r.to_dict() for r in results],
        }
