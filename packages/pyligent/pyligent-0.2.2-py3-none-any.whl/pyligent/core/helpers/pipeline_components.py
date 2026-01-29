from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal, Optional

from datasets import Dataset as HFDataset
from datasets import IterableDataset as HFIterableDataset
from loguru import logger

from pyligent.core import DiligentDataset
from pyligent.core.dataset import DiligentDatasetView
from pyligent.core.explorer import Explorer
from pyligent.core.helpers.log_manager import PipelineLoggingManager
from pyligent.core.path import GoldPath, PathContext
from pyligent.core.solver import Solver
from pyligent.core.validator import Validator

EpochType = int | str
EpochKey = Literal["A", "B", "FINAL"]
GeneralHFDataset = HFDataset | HFIterableDataset


@dataclass
class PipelineConfig:
    gold_paths: list[GoldPath]
    dataset: DiligentDataset
    epochs_a: EpochType = 10
    epochs_b: EpochType = 10
    epochs_final: EpochType = 10
    visualize_dfs: int = 10

    def __post_init__(self):
        self._epoch_dict: dict[EpochKey, EpochType] = {
            "A": self.epochs_a,
            "B": self.epochs_b,
            "FINAL": self.epochs_final,
        }

        try:
            for v in self._epoch_dict.values():
                self._process_epoch(v, t=1)
        except Exception as e:
            raise ValueError("Error with processing epoch") from e

    def _process_epoch(self, epoch: EpochType, t: int) -> int:
        if isinstance(epoch, int):
            return epoch
        return eval(epoch)

    def get_epochs(self, epoch_key: EpochKey, t: int) -> int:
        return self._process_epoch(self._epoch_dict[epoch_key], t=t)


@dataclass
class PhaseResult:
    """Encapsulates the output of a training phase"""

    phase_name: str
    t: int
    metadata: Optional[dict[str, Any]] = None


class TrainingPhase(ABC):
    """Base class for pipeline training phases"""

    @abstractmethod
    def execute(self, context: "PhaseContext") -> PhaseResult:
        pass


@dataclass
class PhaseContext:
    """Shared context passed between phases"""

    solver: Solver
    validator: Validator
    explorer: Explorer
    config: PipelineConfig
    t: int
    gold_paths: list[GoldPath]

    dataset_view: DiligentDatasetView
    hf_dataset: Optional[GeneralHFDataset]  # for finetunning

    loggers: PipelineLoggingManager


class BuildTeacherDatasetPhase(TrainingPhase):
    """Stage 0: Extract prefix-action pairs from gold paths"""

    def execute(self, context: PhaseContext) -> PhaseResult:
        pairs_to_add = []
        for gold_path in context.gold_paths:
            if len(gold_path) >= (context.t + 1):
                prefix = PathContext(
                    gold_path.nodes[: -context.t], gold_length=len(gold_path)
                )
                action = gold_path.nodes[-context.t].action
                pairs_to_add.append((prefix, action))

        context.dataset_view.add_gold_pairs(pairs=pairs_to_add)

        return PhaseResult(
            phase_name="teacher_pairs",
            t=context.t,
            metadata={"source": "gold_paths"},
        )


class SupervisedFinetunePhase(TrainingPhase):
    """Supervised fine-tuning phase (SFT-A or SFT-B)"""

    def __init__(self, phase_name: str, epochs_key: EpochKey, source_description: str):
        self.phase_name = phase_name
        self.epochs_key: EpochKey = epochs_key
        self.source_description = source_description

    def execute(self, context: PhaseContext) -> PhaseResult:
        train_ds = context.hf_dataset
        if train_ds is None:
            raise RuntimeError("Dataset for finetunning is None!")

        epochs = context.config.get_epochs(self.epochs_key, t=context.t)

        finetunning_samples = (
            len(train_ds)
            if isinstance(train_ds, HFDataset)
            else context.dataset_view.store.strategy.max_samples
        )
        logger.log(
            "TITLE",
            f"{self.phase_name} on {finetunning_samples} examples for {epochs} epochs",
        )

        context.solver.finetune(
            train_ds,
            phase=self.phase_name,
            t=context.t,
            epochs=epochs,
        )

        return PhaseResult(
            phase_name=self.phase_name,
            t=context.t,
            metadata={"epochs": epochs, "source": self.source_description},
        )


class ExplorationPhase(TrainingPhase):
    """Stage 2: DFS exploration with bounded search"""

    def execute(self, context: PhaseContext) -> PhaseResult:
        logger.log("TITLE", f"Exploration on {len(context.dataset_view)} examples")

        context.loggers.reset_exploration_phase(context.t)

        gold_pairs = context.dataset_view.gold_pairs
        results = context.explorer.explore(valid_paths=gold_pairs, t=context.t)

        context.loggers.visualize_exploration(
            gold_paths=gold_pairs,
            results=results,
            step_t=context.t,
            visualize_dfs=context.config.visualize_dfs,
        )

        explored_pairs = Explorer.add_to_dataset(context.dataset_view, results)

        context.loggers.log_phase_pairs(
            phase="SFT-B",
            t=context.t,
            explored_pairs=explored_pairs,
            source="exploration",
        )

        return PhaseResult(
            phase_name="exploration",
            t=context.t,
            metadata={
                "num_trajectories": len(results),
                "explored_pairs": len(explored_pairs),
            },
        )
