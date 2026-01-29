from __future__ import annotations

from typing import override

from pyligent.core.action import Action, DoneAction, NodeAction
from pyligent.core.solvers import LlmSolver


class SudokuLlmSolver(LlmSolver):
    @override
    def _parse_action(self, text: str, node_id: int) -> Action:
        action = super()._parse_action(text, node_id)

        # Sudoku-specific HEURISTICS

        # Heuristic 1: If no empty cells -> Done
        if isinstance(action, NodeAction) and "." not in action.text:
            return DoneAction(answer=action.text)

        return action
