from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pyligent.core.dataset import DiligentDatasetItem

if TYPE_CHECKING:
    from pyligent.core.action import Action
    from pyligent.core.path import Node


class TrainingRunLogger:
    """Utility to surface informative logs during training."""

    def __init__(
        self,
        log_path: Path,
        max_phase_examples: int = 5,
        max_exploration_events: int = 10,
        backtrack_log_path: Optional[Path] = None,
        *,
        enable_backtrack_logging: bool = True,
        flush_every: int = 1,
        flush_backtrack_every: int = 1,
    ):
        self.max_phase_examples = max_phase_examples
        self.max_exploration_events = max_exploration_events
        self._exploration_counts: defaultdict[int, int] = defaultdict(int)

        self.log_path = log_path
        self.enable_backtrack_logging = enable_backtrack_logging

        # Flush controls (set >1 to reduce I/O).
        self.flush_every = max(1, int(flush_every))
        self.flush_backtrack_every = max(1, int(flush_backtrack_every))
        self._write_count = 0
        self._backtrack_write_count = 0

        self.backtrack_log_path = (
            backtrack_log_path
            if backtrack_log_path is not None
            else self.log_path.parent
            / f"{self.log_path.stem}_backtracks{self.log_path.suffix}"
        )

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Main log is always enabled (keeps current behavior).
        self._file = self.log_path.open("a", encoding="utf-8")

        # Backtrack log becomes optional.
        self._backtrack_file = None
        if self.enable_backtrack_logging:
            self.backtrack_log_path.parent.mkdir(parents=True, exist_ok=True)
            self._backtrack_file = self.backtrack_log_path.open("a", encoding="utf-8")

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()
        if self._backtrack_file is not None and not self._backtrack_file.closed:
            self._backtrack_file.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._file.write(f"{timestamp} | {level:<8} | {message}\n")
        self._write_count += 1
        if self._write_count % self.flush_every == 0:
            self._file.flush()

    def _write_backtrack(self, message: str) -> None:
        if not self.enable_backtrack_logging or self._backtrack_file is None:
            return
        timestamp = self._timestamp()
        self._backtrack_file.write(f"{timestamp} | BACKTRK | {message}\n")
        self._backtrack_write_count += 1
        if self._backtrack_write_count % self.flush_backtrack_every == 0:
            self._backtrack_file.flush()

    def title(self, message: str) -> None:
        self._write("TITLE", message)

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def success(self, message: str) -> None:
        self._write("SUCCESS", message)

    def warning(self, message: str) -> None:
        self._write("WARNING", message)

    def reset_exploration_phase(self, t: int) -> None:
        """Reset counters for a new exploration phase."""
        self._exploration_counts[t] = 0

    def _format_context(self, nodes: list["Node"]) -> str:
        if not nodes:
            return "[ROOT]"
        return " | ".join(node.action.info_str for node in nodes)

    def _format_tree(
        self, nodes: list["Node"], final_action: Optional["Action"] = None
    ) -> str:
        lines: list[str] = []
        if not nodes:
            lines.append("- [ROOT]")
        for depth, node in enumerate(nodes):
            indent = "  " * depth
            lines.append(f"{indent}- {node.action.info_str}")
        if final_action is not None:
            indent = "  " * len(nodes)
            lines.append(f"{indent}- {final_action.info_str}")
        return "\n".join(lines) if lines else "- [ROOT]"

    def log_phase_pairs(
        self,
        phase: str,
        t: int,
        explored_pairs: list[DiligentDatasetItem],
        source: str = "dataset",
    ) -> None:
        """Log sample training trees for a phase."""
        total = len(explored_pairs)
        if total == 0:
            self.info(f"[{phase} t={t}] No training pairs for {source}")
            return

        limit = min(self.max_phase_examples, total)
        self.title(f"{phase} t={t} {source} training pairs (showing {limit} of {total})")
        for idx, (prefix, action) in enumerate(islice(explored_pairs, limit), start=1):
            tree_str = self._format_tree(prefix.nodes, action)
            self.info(f"(Tree #{idx})\n{tree_str}")

    def log_exploration_action(
        self,
        t: int,
        depth: int,
        nodes: list["Node"],
        action: "Action",
        passed: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Log validator outcome for a generated action during exploration."""
        if self.max_exploration_events <= 0:
            return

        count = self._exploration_counts[t]
        if count >= self.max_exploration_events:
            if count == self.max_exploration_events:
                self.info(
                    f"[SFT-B t={t}] Reached exploration logging cap "
                    f"({self.max_exploration_events}). Further events suppressed."
                )
                self._exploration_counts[t] += 1
            return

        context_str = self._format_context(nodes)
        action_type = type(action).__name__
        status = "PASS" if passed else "FAIL"
        header = (
            f"[SFT-B t={t} depth={depth}] {status} validator | "
            f"{action_type}: {action.info_str}"
        )
        if passed:
            self.success(f"{header}\nContext: {context_str}")
        else:
            reason_msg = f"Reason: {reason}" if reason else "Reason: validator rejection"
            self.warning(f"{header}\nContext: {context_str}\n{reason_msg}")

        self._exploration_counts[t] += 1

    def log_backtrack_event(
        self,
        *,
        phase: str,
        t: int,
        depth: int,
        path_nodes: list["Node"],
        backtrack_action: "Action",
        raw_path_nodes: Optional[list["Node"]] = None,
    ) -> None:
        """Record a validator-triggered backtrack with full path context."""
        if not self.enable_backtrack_logging:
            return

        reason = getattr(backtrack_action, "reason", None)
        reason_str = reason if reason else "No reason provided"
        tree_str = self._format_tree(path_nodes)
        action_str = getattr(backtrack_action, "info_str", str(backtrack_action))
        message = (
            f"[{phase} t={t} depth={depth}] Backtrack issued\n"
            f"Reason: {reason_str}\n"
            f"Path leading to backtrack:\n{tree_str}\n"
            f"Backtrack action: {action_str}"
        )
        if raw_path_nodes is not None:
            raw_tree = self._format_tree(raw_path_nodes)
            message = f"{message}\nOriginal path (pre-renumbering):\n{raw_tree}"
        self._write_backtrack(message)
