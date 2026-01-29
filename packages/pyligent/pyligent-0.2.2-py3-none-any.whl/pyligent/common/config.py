import argparse
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

import yaml
from loguru import logger
from typing_extensions import Literal

from pyligent.common.utils.global_config import apply_global_config
from pyligent.common.utils.logger import LogLevel
from pyligent.core.explorer import ExploreTechniques
from pyligent.core.helpers.logging_config import PipelineLoggingConfig
from pyligent.core.helpers.pipeline_components import EpochType


@dataclass
class DataConfig:
    """Dataset configuration."""

    max_examples: Optional[int] = None


@dataclass
class ModelConfig:
    """Model and training configuration."""

    model_name: str = "Qwen/Qwen3-0.6B"
    use_qlora: bool = True
    bf16: bool = True
    lr: float = 2e-5
    max_seq_len: int = 2048
    chat_mode: Literal["user", "assistant"] = "user"
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    use_k_sequences: bool = True

    def to_solver_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for solver initialization."""
        return asdict(self)


@dataclass
class TrainingConfig:
    """Training epochs configuration."""

    epochs_a: EpochType = 3
    epochs_b: EpochType = 2
    epochs_final: EpochType = 5
    checkpoint_save_steps: int = 100
    checkpoint_save_total_limit: int = 5

    def to_solver_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for solver initialization."""
        return {
            "checkpoint_save_steps": self.checkpoint_save_steps,
            "checkpoint_save_total_limit": self.checkpoint_save_total_limit,
        }


@dataclass
class ExplorationConfig:
    """Exploration configuration."""

    # Which explorer implementation to use
    explorer_type: Literal["linear", "dendritic", "sampling"] = "linear"

    # Shared exploration params
    B: int = 3
    Tmax: int = 5
    c_leaf: float = 3
    max_leaf_capability: Optional[int] = None

    # Does not matter for Linear Explorer
    # Note: SamplingExplorer will also derive its capacity_mode from this field.
    mode: ExploreTechniques = "exponential"

    # Batching / depth control / policies
    explore_batch_size: int = 128
    adaptive_tmax: bool = True
    adaptive_tmax_buffer: int = 0
    deduplication: bool = True
    allow_backtracks: bool = False
    always_renumber_node_id: bool = True
    afterwards_backtrack_target: bool = True

    # --- BaseDendritic hyperparameters ---
    sampling_transition_point: float = 2.0
    sampling_h: float = 2.0
    sampling_alpha_bfs: float = -1.0
    sampling_alpha_dfs: float = 1.0
    sampling_beta: float = 1.0
    sampling_epsilon: float = 1e-6
    sampling_nodes: Optional[int] = None  # None == B

    # --- Dendritic hyperparameters ---
    sampling_strategy: Literal["prefer_nodes", "prefer_children"] = "prefer_nodes"

    # --- Sampling hyperparameters ---
    sampling_temperature: float = 1.0
    seed: Optional[int] = None

    def to_explorer_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for explorer initialization (excluding state_engine)."""
        return asdict(self)


@dataclass
class GenerationConfig:
    """Text generation configuration."""

    num_samples: int = 4
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.8
    repetition_penalty: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for solver."""
        return {
            "num_return_sequences": self.num_samples,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
        }


@dataclass
class ValidatorConfig:
    """Base validator configuration."""

    pass


@dataclass
class LoggingConfig:
    """Logging and output configuration."""

    verbose: bool = False
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    log_file: str = "log.log"
    level: LogLevel = "INFO"
    datetime_logfile: bool = False
    visualize_dfs: int = 10  # How many DFS visualize (0 - all)
    ignore_warnings: bool = True

    # Backtrack + flush controls
    enable_backtrack_logging: bool = True
    flush_every: int = 1
    flush_backtrack_every: int = 1

    save_composite_dataset: bool = True
    save_gold_paths_summary: bool = True

    # --- Unified pipeline logger manager toggles ---
    enable_training_run_logger: bool = True
    enable_tensorboard_eval_logger: bool = True
    enable_dfs_visualizer: bool = True

    # TrainingRunLogger verbosity limits
    train_logger_max_phase_examples: int = 5
    train_logger_max_exploration_events: int = 10

    # Validator hook log toggles
    enable_prm_logging: bool = True
    enable_llm_logging: bool = True

    def to_training_logger_kwargs(self) -> dict[str, object]:
        return {
            "enable_backtrack_logging": self.enable_backtrack_logging,
            "flush_every": self.flush_every,
            "flush_backtrack_every": self.flush_backtrack_every,
        }

    def to_pipeline_logging_config(self) -> PipelineLoggingConfig:
        return PipelineLoggingConfig(
            enable_training_run_logger=self.enable_training_run_logger,
            enable_tensorboard_eval_logger=self.enable_tensorboard_eval_logger,
            enable_dfs_visualizer=self.enable_dfs_visualizer,
            max_phase_examples=self.train_logger_max_phase_examples,
            max_exploration_events=self.train_logger_max_exploration_events,
            enable_backtrack_logging=self.enable_backtrack_logging,
            flush_every=self.flush_every,
            flush_backtrack_every=self.flush_backtrack_every,
            enable_prm_logging=self.enable_prm_logging,
            enable_llm_logging=self.enable_llm_logging,
        )


@dataclass
class DiligentDatasetConfig:
    """YAML-serializable dataset config used by PipelineConfig."""

    sampling_strategy: Literal["default", "cumulative", "all"] = "default"
    seed: Optional[int] = 0
    check_uniqueness: bool = True
    max_samples: Optional[int] = None
    shuffle: bool = True

    def __post_init__(self) -> None:
        if self.seed is None:
            self.seed = 0


@dataclass
class ScriptConfig:
    """Complete pipeline configuration."""

    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    exploration: ExplorationConfig = field(default_factory=ExplorationConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    validator: ValidatorConfig = field(default_factory=ValidatorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    dataset: DiligentDatasetConfig = field(default_factory=DiligentDatasetConfig)
    env: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "ScriptConfig":
        """Create config from nested dictionary"""

        return cls(
            data=DataConfig(**config_dict.get("data", {})),
            model=ModelConfig(**config_dict.get("model", {})),
            training=TrainingConfig(**config_dict.get("training", {})),
            exploration=ExplorationConfig(**config_dict.get("exploration", {})),
            generation=GenerationConfig(**config_dict.get("generation", {})),
            validator=ValidatorConfig(**config_dict.get("validator", {})),
            logging=LoggingConfig(**config_dict.get("logging", {})),
            dataset=DiligentDatasetConfig(**config_dict.get("dataset", {})),
            env=config_dict.get("env", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to nested dictionary."""
        return {
            "data": asdict(self.data),
            "model": asdict(self.model),
            "training": asdict(self.training),
            "exploration": asdict(self.exploration),
            "generation": asdict(self.generation),
            "validator": asdict(self.validator),
            "logging": asdict(self.logging),
            "dataset": asdict(self.dataset),
            "env": self.env,
        }

    def update_from_dict(self, override_dict: dict[str, Any]) -> None:
        """Update configuration from nested dictionary (in-place)."""
        for section, values in override_dict.items():
            if hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
                    elif isinstance(section_obj, dict):
                        section_obj[key] = value
                    else:
                        logger.warning(f"Unknown config key: {section}.{key}, ignoring")
            else:
                logger.warning(f"Unknown config section: {section}, ignoring")

    def apply_cli_overrides(self, args: argparse.Namespace) -> None:
        """Apply command-line argument overrides to config."""
        if args.output_dir is not None:
            self.logging.output_dir = args.output_dir

        if args.verbose is not None:
            self.logging.level = "INFO"

        if getattr(args, "save_steps", None) is not None:
            self.training.checkpoint_save_steps = args.save_steps


TScriptConfig = TypeVar("TScriptConfig", bound=ScriptConfig)


def load_config(
    default_config_path: Optional[Path] = None,
    user_config_path: Optional[Path] = None,
    script_cls: Type[TScriptConfig] = ScriptConfig,  # type: ignore
) -> TScriptConfig:
    """
    Load configuration with hierarchical override.

    Args:
        default_config_path: Path to default YAML config
        user_config_path: Path to user override YAML config
        script_cls: Config class to instantiate

    Returns:
        Complete ScriptConfig with all overrides applied
    """
    config = script_cls()

    if default_config_path and default_config_path.exists():
        logger.info(f"Loading default config from {default_config_path}")
        with open(default_config_path, "r", encoding="utf-8") as f:
            default_dict = yaml.safe_load(f) or {}
        config.update_from_dict(default_dict)
    elif default_config_path:
        logger.warning(f"Default config not found: {default_config_path}")

    if user_config_path and user_config_path.exists():
        logger.info(f"Loading user config from {user_config_path}")
        with open(user_config_path, "r", encoding="utf-8") as f:
            user_dict = yaml.safe_load(f) or {}
        config.update_from_dict(user_dict)
    elif user_config_path:
        logger.warning(f"User config not found: {user_config_path}")

    return config


def setup_environment(config: ScriptConfig) -> None:
    """
    Setup environment variables and global configurations.

    Should be called once after config is loaded, before training starts.
    """
    if config.env:
        for variable, value in config.env.items():
            if len(str(value)) > 0:
                os.environ[variable] = str(value)
        logger.info(f"Applied {len(config.env)} environment variables")

    apply_global_config()

    if config.logging.ignore_warnings:
        import warnings

        warnings.filterwarnings("ignore")
        logger.info("Warnings suppressed")


def save_config(config: ScriptConfig, output_path: Path) -> None:
    """Save configuration to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
    logger.info(f"Configuration saved to {output_path}")
