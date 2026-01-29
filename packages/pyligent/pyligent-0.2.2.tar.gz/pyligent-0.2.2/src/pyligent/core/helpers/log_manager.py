from __future__ import annotations

from pathlib import Path
from typing import Optional

from loguru import logger
from transformers.utils import logging as hf_logging

from pyligent.common.tensorboard_logger import TensorBoardLogger
from pyligent.common.visualize import DFSVisualizer
from pyligent.core.dataset import DiligentDatasetItem
from pyligent.core.explorer import ExploreResult
from pyligent.core.helpers.logging_config import PipelineLoggingConfig
from pyligent.core.helpers.training_logger import TrainingRunLogger


class NullTensorBoardLogger:
    """Drop-in replacement to keep eval-hook call sites simple."""

    def log_phase_data_single(
        self,
        phase: int,
        example_num: int,
        context: str,
        expected: str,
        predicted: str,
        is_valid: bool,
    ) -> None:
        return


class PipelineLoggingManager:
    """
    Single owner for all pipeline-related loggers.

    Pipeline/phases/explorer call this unified interface so new sinks can be added
    without wiring multiple objects through the codebase.
    """

    def __init__(
        self,
        *,
        log_dir: Path,
        solver_out_dir: Path,
        time_stamp: str,
        config: PipelineLoggingConfig,
        visualizer_kwargs: Optional[dict] = None,
    ) -> None:
        self.log_dir = log_dir
        self.solver_out_dir = solver_out_dir
        self.time_stamp = time_stamp
        self.config = config

        self._training_log_dir = self.log_dir / "training_logs"
        self._training_log_dir.mkdir(parents=True, exist_ok=True)

        self.training_log_path = self._training_log_dir / f"{self.time_stamp}.log"
        self._dfs_dir = self.log_dir / "dfs"

        # 1) Main training log file (optional)
        self.train: Optional[TrainingRunLogger] = None
        if self.config.enable_training_run_logger:
            self.train = TrainingRunLogger(
                self.training_log_path,
                max_phase_examples=self.config.max_phase_examples,
                max_exploration_events=self.config.max_exploration_events,
                enable_backtrack_logging=self.config.enable_backtrack_logging,
                flush_every=self.config.flush_every,
                flush_backtrack_every=self.config.flush_backtrack_every,
            )

        # 2) TensorBoard eval logger (optional)
        if self.config.enable_tensorboard_eval_logger:
            self.tensorboard: TensorBoardLogger | NullTensorBoardLogger = (
                TensorBoardLogger(self.solver_out_dir, self.time_stamp)
            )
        else:
            self.tensorboard = NullTensorBoardLogger()

        # 3) DFS visualizer (optional)
        self.dfs: Optional[DFSVisualizer] = None
        if self.config.enable_dfs_visualizer:
            self._dfs_dir.mkdir(parents=True, exist_ok=True)
            self.dfs = DFSVisualizer(
                output_dir=self._dfs_dir, **(visualizer_kwargs or {})
            )

        # Keep HF trainer noise down.
        hf_logging.set_verbosity_warning()

    # --- Unified interface: run log methods (no-op when disabled) ---

    def title(self, message: str) -> None:
        if self.train is not None:
            self.train.title(message)

    def info(self, message: str) -> None:
        if self.train is not None:
            self.train.info(message)

    def success(self, message: str) -> None:
        if self.train is not None:
            self.train.success(message)

    def warning(self, message: str) -> None:
        if self.train is not None:
            self.train.warning(message)

    def reset_exploration_phase(self, t: int) -> None:
        if self.train is not None:
            self.train.reset_exploration_phase(t)

    def log_phase_pairs(
        self,
        phase: str,
        t: int,
        explored_pairs: list[DiligentDatasetItem],
        source: str = "dataset",
    ) -> None:
        if self.train is not None:
            self.train.log_phase_pairs(
                phase=phase, t=t, explored_pairs=explored_pairs, source=source
            )

    def log_backtrack_event(self, **kwargs) -> None:
        if self.train is not None:
            self.train.log_backtrack_event(**kwargs)

    # --- DFS visualization ---

    def visualize_exploration(
        self,
        *,
        gold_paths: list[DiligentDatasetItem],
        results: list[ExploreResult],
        step_t: int,
        visualize_dfs: int,
    ) -> None:
        if self.dfs is None:
            return

        if visualize_dfs > 0:
            results_subset = results[:visualize_dfs]
        else:
            results_subset = results

        if not results_subset:
            return

        prefix_ctxs = [gold_paths[i][0] for i in range(len(results_subset))]
        solutions, failed_leaves = map(list, zip(*results_subset))
        self.dfs.visualize(prefix_ctxs, solutions, failed_leaves, step_t=step_t)

    # --- Validator hook logs (kept here because they produce files) ---

    def setup_validator_logging_hooks(self, validator) -> None:
        if self.config.enable_prm_logging:
            prm_hook = getattr(validator, "enable_prm_logging", None)
            if callable(prm_hook):
                prm_log_path = (
                    self._training_log_dir / f"{self.time_stamp}_prm_scores.jsonl"
                )
                try:
                    prm_hook(prm_log_path)
                    logger.info(f"PRM score log file: {prm_log_path}")
                except Exception as exc:
                    logger.warning(f"Failed to initialize PRM logging: {exc}")

        if self.config.enable_llm_logging:
            llm_hook = getattr(validator, "enable_llm_logging", None)
            if callable(llm_hook):
                llm_log_path = (
                    self._training_log_dir / f"{self.time_stamp}_llm_verdicts.jsonl"
                )
                try:
                    llm_hook(llm_log_path)
                    logger.info(f"LLM validator log file: {llm_log_path}")
                except Exception as exc:
                    logger.warning(f"Failed to initialize LLM logging: {exc}")

    def close(self) -> None:
        if self.train is not None:
            self.train.close()
