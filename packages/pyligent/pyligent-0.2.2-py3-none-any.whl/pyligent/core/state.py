from abc import ABC, abstractmethod
from typing import Optional

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction


class StateEngine(ABC):
    """Abstract base for computing node state from parent state and action."""

    @abstractmethod
    def reduce[T](self, parent_state: Optional[T], action: Action) -> T:
        """
        Compute new state by reducing parent_state with action.

        Args:
            parent_state: State from parent node (None for root)
            action: Action being applied

        Returns:
            New state for the child node
        """


class TextConcatStateEngine(StateEngine):
    """Default implementation: concatenate text from NodeActions."""

    def reduce(self, parent_state: Optional[str], action: Action) -> str:
        """Concatenate action text to parent state."""
        prev_text = "" if parent_state is None else str(parent_state)

        if isinstance(action, NodeAction):
            new_text = action.text
            return f"{prev_text}\n{new_text}".strip()

        if isinstance(action, DoneAction):
            # return (prev_text + "\n[ANSWER] " + action.answer).strip()
            return f"{prev_text}\n{action.answer}".strip()

        if isinstance(action, BacktrackAction):
            # Backtrack doesn't modify state
            return prev_text

        return prev_text
