from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineLoggingConfig:
    # Core toggles
    enable_training_run_logger: bool = True
    enable_tensorboard_eval_logger: bool = True
    enable_dfs_visualizer: bool = True

    # TrainingRunLogger controls (I/O + verbosity caps)
    max_phase_examples: int = 5
    max_exploration_events: int = 10
    enable_backtrack_logging: bool = True
    flush_every: int = 1
    flush_backtrack_every: int = 1

    # Validator hook logs
    enable_prm_logging: bool = True
    enable_llm_logging: bool = True
