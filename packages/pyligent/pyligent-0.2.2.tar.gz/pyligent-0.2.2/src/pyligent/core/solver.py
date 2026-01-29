import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from datasets import Dataset
from datasets import Dataset as HFDataset
from datasets import IterableDataset as HFIterableDataset

from pyligent.core.action import Action, NodeAction
from pyligent.core.helpers.action_parser import ActionParser
from pyligent.core.path import PathContext

GeneralHFDataset = HFDataset | HFIterableDataset


class Solver(ABC):
    """Abstract solver that proposes candidate actions and manages node IDs."""

    def __init__(
        self,
        out_dir: Path = Path("output"),
    ) -> None:
        super().__init__()
        self.time_stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.out_dir = out_dir

    def _parse_action(self, text: str, node_id: int) -> Action:
        return ActionParser.parse(text, node_id=node_id)

    @abstractmethod
    def propose_actions(
        self,
        *,
        contexts: list[PathContext],
        t: int,
        max_actions: int = 1,
    ) -> tuple[list[list[Action | str]], int]:
        """
        Return candidate actions for the given path-only context.
        If max_actions > 0, limit returned list to at most max_actions.
        """

    def propose_actions_processed(
        self, *, contexts: list[PathContext], t: int, max_actions: int = 1
    ) -> tuple[list[list[Action]], int]:
        """
        Process raw solver outputs and normalize node IDs.

        - Convert strings to Action objects
        - Fill None node_id values with sequential integers
        - Ensure all NodeActions have valid int node_id
        """
        proposed_actions, solver_calls = self.propose_actions(
            contexts=contexts, t=t, max_actions=max_actions
        )

        processed_actions: list[list[Action]] = []

        for ctx, acts in zip(contexts, proposed_actions):
            prev = ctx.previous_node_action_id
            current_id = prev + 1
            normalized: list[Action] = []

            for action in acts:
                # Parse string actions
                if isinstance(action, str):
                    action = self._parse_action(action, node_id=current_id)

                # Normalize NodeAction with None or missing node_id
                if isinstance(action, NodeAction):
                    # Check if node_id is None or invalid
                    provided_id = getattr(action, "node_id", None)
                    if provided_id is None:
                        action = NodeAction(current_id, action.text)
                        current_id += 1
                    else:
                        # Ensure it's an int
                        action = NodeAction(int(provided_id), action.text)

                normalized.append(action)

            processed_actions.append(normalized)

        return processed_actions, solver_calls

    @abstractmethod
    def finetune(
        self,
        dataset: GeneralHFDataset,
        epochs: int,
        t: int,
        eval_dataset: Optional[Dataset] = None,
        phase: str = "SFT-A",
        **kwargs,
    ):
        """
        Finetune the solver on the provided dataset for a number of epochs.

        Args:
            dataset: HuggingFace dataset
            epochs: Number of epochs to finetune
            t: Current exploration depth/iteration
            eval_dataset: Optional evaluation dataset
            phase: Current training phase ("SFT-A", "SFT-B", "Final")
        """

    def save(self, output_dir: Path, metadata: Optional[dict] = None):
        pass
