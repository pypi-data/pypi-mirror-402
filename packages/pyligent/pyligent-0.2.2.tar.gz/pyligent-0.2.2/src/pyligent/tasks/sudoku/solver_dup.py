from __future__ import annotations

from pyligent.core.action import Action
from pyligent.core.path import PathContext
from pyligent.tasks.sudoku.solver import SudokuLlmSolver as BasicSudokuSolver


class SudokuLlmSolver(BasicSudokuSolver):
    def propose_actions(
        self, contexts: list[PathContext], max_actions: int = 0
    ) -> tuple[list[list[Action | str]], int]:
        return (
            [
                [
                    "16428597191536724887241936575963148242357861918692475369875213454719382623.846597"
                    for j in range(max_actions or 1)
                ]
                for i in range(len(contexts))
            ],
            1,
        )
