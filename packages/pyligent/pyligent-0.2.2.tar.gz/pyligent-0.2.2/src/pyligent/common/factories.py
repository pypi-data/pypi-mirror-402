from pathlib import Path
from typing import Any

from loguru import logger

from pyligent.common.config import (
    DiligentDatasetConfig,
    ExplorationConfig,
    GenerationConfig,
    ModelConfig,
    TrainingConfig,
)
from pyligent.core import DiligentDataset
from pyligent.core.dataset import ParquetDatasetConfig
from pyligent.core.datasets.sampling_strategies import (
    AllDataStrategy,
    CumulativeUpToTStrategy,
    DefaultSamplingStrategy,
)
from pyligent.core.explorer import Explorer
from pyligent.core.explorers import (
    DendriticExplorer,
    DendriticExplorerConfig,
    LinearExplorer,
    LinearExplorerConfig,
    SamplingExplorer,
    SamplingExplorerConfig,
)
from pyligent.core.state import StateEngine


class DatasetFactory:
    """Factory for creating DiligentDataset."""

    @staticmethod
    def create(
        *,
        dataset_config: DiligentDatasetConfig,
        output_dir: Path,
        **extra_kwargs: Any,
    ) -> DiligentDataset:
        sampling_strategy = dataset_config.sampling_strategy
        logger.info(
            f"Initializing dataset with sampling strategy '{sampling_strategy}'..."
        )

        if dataset_config.max_samples is not None:
            logger.warning(
                "'max_samples' is set, so IterableDataset will be used. Also, only #max_samples rows will be saved as finetunning snapshot"
            )

        common_samplig_kwargs = dict(
            max_samples=dataset_config.max_samples,
            shuffle=dataset_config.shuffle,
        )

        if sampling_strategy == "default":
            sampling_strategy = DefaultSamplingStrategy(
                **common_samplig_kwargs  # ty:ignore[invalid-argument-type]
            )

        elif sampling_strategy == "cumulative":
            sampling_strategy = CumulativeUpToTStrategy(**common_samplig_kwargs)  # ty:ignore[invalid-argument-type]
        elif sampling_strategy == "all":
            sampling_strategy = AllDataStrategy(**common_samplig_kwargs)  # ty:ignore[invalid-argument-type]
            logger.warning(
                f"Strategy '{sampling_strategy}' can result in huge resources usage!"
            )
        else:
            raise ValueError(f"Unknown sampling_strategy: '{sampling_strategy}'.")

        dataset = DiligentDataset(
            root_dir=Path(output_dir),
            config=ParquetDatasetConfig(
                seed=dataset_config.seed,
                check_uniqueness=bool(dataset_config.check_uniqueness),
            ),
            strategy=sampling_strategy,
        )

        logger.info("Dataset initialized successfully\n")
        return dataset


class SolverFactory:
    """Factory for creating LLM solvers."""

    @staticmethod
    def create(
        solver_class: type,
        model_config: ModelConfig,
        training_config: TrainingConfig,
        generation_config: GenerationConfig,
        output_dir: Path,
        **extra_kwargs: Any,
    ):
        logger.info("Initializing solver with QLoRA...")
        logger.info(f"Model: {model_config.model_name}")
        logger.info(f"Learning rate: {model_config.lr}")
        logger.info(f"Max sequence length: {model_config.max_seq_len}")
        logger.info(f"QLoRA enabled: {model_config.use_qlora}")

        solver_kwargs = {
            **model_config.to_solver_kwargs(),
            **training_config.to_solver_kwargs(),
            "out_dir": output_dir,
            "gen_cfg": generation_config.to_dict(),
            **extra_kwargs,
        }

        solver = solver_class(**solver_kwargs)
        logger.info("Solver initialized\n")
        return solver


class ExplorerFactory:
    """Factory for creating explorers based on config."""

    @staticmethod
    def create(
        exploration_config: ExplorationConfig,
        state_engine: StateEngine,
    ) -> Explorer:
        explorer_type = exploration_config.explorer_type
        logger.info(f"Initializing {explorer_type} explorer...")

        if explorer_type == "linear":
            explorer = ExplorerFactory._create_linear_explorer(
                exploration_config, state_engine
            )
        elif explorer_type == "dendritic":
            explorer = ExplorerFactory._create_dendritic_explorer(
                exploration_config, state_engine
            )
        elif explorer_type == "sampling":
            explorer = ExplorerFactory._create_sampling_explorer(
                exploration_config, state_engine
            )
        else:
            raise ValueError(
                f"Unknown explorer type: {explorer_type}. Must be one of: 'linear', 'sampling'"
            )

        logger.info(
            f"Explorer initialized with B={exploration_config.B}, "
            f"Tmax={exploration_config.Tmax}, c_leaf={exploration_config.c_leaf}, "
            f"adaptive_tmax={exploration_config.adaptive_tmax}\n"
        )
        return explorer

    @staticmethod
    def _common_kwargs(
        cfg: ExplorationConfig, state_engine: StateEngine
    ) -> dict[str, Any]:
        """
        Common kwargs for modern ExplorerConfig-derived configs.

        Note: cfg.mode maps to ExplorerConfig.max_actions_strategy (solver proposal schedule).
        """
        return {
            "branching_factor": cfg.B,
            "max_depth": cfg.Tmax,
            "leaf_budget_multiplier": cfg.c_leaf,
            "max_leaf_capability": cfg.max_leaf_capability,
            "max_actions_strategy": cfg.mode,
            "explore_batch_size": cfg.explore_batch_size,
            "adaptive_max_depth": cfg.adaptive_tmax,
            "adaptive_max_depth_buffer": cfg.adaptive_tmax_buffer,
            "allow_backtracks": cfg.allow_backtracks,
            "always_renumber_node_id": cfg.always_renumber_node_id,
            "state_engine": state_engine,
            "deduplication": cfg.deduplication,
            "afterwards_backtrack_target": cfg.afterwards_backtrack_target,
        }

    @staticmethod
    def _common_dendritic_kwargs(
        cfg: ExplorationConfig, state_engine: StateEngine
    ) -> dict[str, Any]:
        """
        Common kwargs for modern BaseDendriticExplorerConfigconfigs.
        """
        return {
            **ExplorerFactory._common_kwargs(cfg, state_engine),
            "sampling_transition_point": cfg.sampling_transition_point,
            "h": cfg.sampling_h,
            "alpha_bfs": cfg.sampling_alpha_bfs,
            "alpha_dfs": cfg.sampling_alpha_dfs,
            "beta": cfg.sampling_beta,
            "epsilon": cfg.sampling_epsilon,
            "sampling_nodes": cfg.sampling_nodes,
            "capacity_mode": ExplorerFactory._derived_capacity_mode(cfg),
        }

    @staticmethod
    def _derived_capacity_mode(cfg: ExplorationConfig) -> str:
        """
        SamplingExplorer needs capacity_mode to compute Gap_i = c_max(i) - c_i.

        We derive it from cfg.mode to avoid introducing an extra global parameter:
        - mode == "exponential" -> capacity_mode="exponential"
        - otherwise -> capacity_mode="linear"
        """
        return "exponential" if cfg.mode == "exponential" else "linear"

    @staticmethod
    def _create_linear_explorer(
        cfg: ExplorationConfig, state_engine: StateEngine
    ) -> Explorer:
        # LinearExplorer defines its own capacity rule (root=B, others=1), so it does NOT need capacity_mode.
        kwargs = ExplorerFactory._common_kwargs(cfg, state_engine)
        return LinearExplorer(LinearExplorerConfig(**kwargs))

    @staticmethod
    def _create_dendritic_explorer(
        cfg: ExplorationConfig, state_engine: StateEngine
    ) -> Explorer:
        kwargs = {
            **ExplorerFactory._common_dendritic_kwargs(cfg, state_engine),
            # Dendritic-specific params
            "sampling_strategy": cfg.sampling_strategy,
        }
        return DendriticExplorer(DendriticExplorerConfig(**kwargs))  # type: ignore

    @staticmethod
    def _create_sampling_explorer(
        cfg: ExplorationConfig, state_engine: StateEngine
    ) -> Explorer:
        kwargs = {
            **ExplorerFactory._common_dendritic_kwargs(cfg, state_engine),
            # Sampling-specific params
            "temperature": cfg.sampling_temperature,
            "seed": None,
        }
        return SamplingExplorer(SamplingExplorerConfig(**kwargs))  # type: ignore
