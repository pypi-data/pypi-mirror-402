from pathlib import Path
from typing import Optional

from loguru import logger

from pyligent.core.dataset import AllDataStrategy, DiligentDataset
from pyligent.core.explorer import Explorer
from pyligent.core.helpers.log_manager import (
    PipelineLoggingConfig,
    PipelineLoggingManager,
)
from pyligent.core.helpers.pipeline_components import (
    BuildTeacherDatasetPhase,
    ExplorationPhase,
    PhaseContext,
    PipelineConfig,
    SupervisedFinetunePhase,
)
from pyligent.core.solver import Solver
from pyligent.core.validator import Validator


class Pipeline:
    """Orchestrates the Diligent Learner training pipeline"""

    def __init__(
        self,
        solver: Solver,
        validator: Validator,
        explorer: Explorer,
        output_dir: Path | str,
        visualizer_kwargs: Optional[dict] = None,
        *,
        loggers: Optional[PipelineLoggingManager] = None,
        logger_config: Optional[PipelineLoggingConfig] = None,
    ):
        self.solver = solver
        self.validator = validator
        self.explorer = explorer
        self.log_dir = Path(output_dir)

        if loggers is not None:
            self.loggers = loggers
        else:
            if logger_config is None:
                raise ValueError(
                    "Either `loggers` must be provided, or `logger_config` must be provided."
                )
            self._setup_logging(
                logger_config=logger_config,
                visualizer_kwargs=visualizer_kwargs,
            )

        self._setup_phases()

        self.explorer.build(self.solver, self.validator)
        self.explorer.set_training_logger(self.loggers)
        self.loggers.setup_validator_logging_hooks(self.validator)

        logger.info(f"Detailed training log file: {self.loggers.training_log_path}")

    def _setup_logging(
        self,
        *,
        logger_config: PipelineLoggingConfig,
        visualizer_kwargs: Optional[dict] = None,
    ) -> None:
        self.loggers = PipelineLoggingManager(
            log_dir=self.log_dir,
            solver_out_dir=self.solver.out_dir,
            time_stamp=self.solver.time_stamp,
            config=logger_config,
            visualizer_kwargs=visualizer_kwargs,
        )

    def _setup_phases(self):
        self.phases = {
            "build_teacher": BuildTeacherDatasetPhase(),
            "sft_a": SupervisedFinetunePhase("SFT-A", "A", "teacher"),
            "exploration": ExplorationPhase(),
            "sft_b": SupervisedFinetunePhase("SFT-B", "B", "cumulative"),
            "final": SupervisedFinetunePhase("Final", "FINAL", "full"),
        }

    def run(self, config: PipelineConfig) -> DiligentDataset:
        """Execute the complete training pipeline."""
        max_chain_length = max(len(g) for g in config.gold_paths)
        self.dataset = config.dataset

        context = PhaseContext(
            solver=self.solver,
            validator=self.validator,
            explorer=self.explorer,
            config=config,
            t=1,
            gold_paths=config.gold_paths,
            dataset_view=self.dataset.at(1),
            hf_dataset=None,
            loggers=self.loggers,
        )

        for t in range(1, max_chain_length):
            logger.log("SECTION", f"Pipeline iteration t={t}/{max_chain_length - 1}")
            context.dataset_view = self.dataset.at(t)
            context.t = t
            self._execute_iteration(context)

        self._execute_final_phase(context, max_chain_length)

        self.dataset.flush()

        # Export a single, non-partitioned Parquet
        self.dataset.export_single_parquet()

        return self.dataset

    def _execute_iteration(self, context: PhaseContext):
        # Stage 0: Build teacher dataset into in-memory view + parquet
        self.phases["build_teacher"].execute(context)
        self.dataset.flush()

        # Stage 1: SFT-A (gold only for t)
        context.hf_dataset = self.dataset.materialize_hf(
            t=context.t,
            only_gold=True,
        )
        self.phases["sft_a"].execute(context)

        # Stage 2: Exploration uses in-memory view
        self.phases["exploration"].execute(context)
        self.dataset.flush()

        # Stage 3: SFT-B (gold + explored for t)
        context.hf_dataset = self.dataset.materialize_hf(
            t=context.t,
            only_gold=False,
        )
        self.phases["sft_b"].execute(context)

    def _execute_final_phase(self, context: PhaseContext, max_chain_length: int):
        context.t = max_chain_length

        context.hf_dataset = self.dataset.materialize_hf(
            t=context.t,
            only_gold=False,
            strategy=AllDataStrategy(
                max_samples=self.dataset.strategy.max_samples,
                shuffle=self.dataset.strategy.shuffle,
            ),
        )
        self.phases["final"].execute(context)
