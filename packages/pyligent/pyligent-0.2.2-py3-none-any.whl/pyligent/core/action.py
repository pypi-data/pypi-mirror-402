"""Action classes for structured reasoning steps."""

from abc import ABC, abstractmethod
from typing import Optional, override


class Action(ABC):
    """Base class for structured actions (<node>, <backtrack>, <done>)."""

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def dense_str(self) -> str:
        return str(self)

    @property
    def hash_value(self) -> int:
        return hash(self.dense_str)

    @property
    def info_str(self) -> str:
        return str(self)


class NodeAction(Action):
    """Reasoning step action with sequential ID and content."""

    __slots__ = ("node_id", "_text")

    def __init__(self, node_id: int, text: str):
        self.node_id = int(node_id)  # Enforce int type
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def __str__(self):
        return f"<node>{self.node_id} {self.text}</node>"

    @property
    @override
    def dense_str(self) -> str:
        return f"n:{self.node_id}:{self.text}"


class BacktrackAction(Action):
    """Backtrack to a previous NodeAction by ID."""

    __slots__ = ("target_id", "reason")

    def __init__(self, target_id: int, reason: Optional[str] = None):
        self.target_id = int(target_id)
        self.reason = reason or f"backtrack to {target_id}"

    @property
    def text(self) -> str:
        return ""

    def __str__(self):
        return f"<backtrack>{self.target_id}</backtrack>"

    @property
    @override
    def dense_str(self) -> str:
        return f"b:{self.target_id}"

    @property
    @override
    def info_str(self) -> str:
        if self.reason is None:
            return str(self)
        return f"<backtrack>{self.target_id}</backtrack> | {self.reason}"


class DoneAction(Action):
    """Terminal action with final answer."""

    __slots__ = ("answer",)

    def __init__(self, answer: str):
        self.answer = answer

    @property
    def text(self) -> str:
        return self.answer

    def __str__(self):
        return f"<done>{self.text}</done>"

    @property
    @override
    def dense_str(self) -> str:
        return f"d:{self.text}"
