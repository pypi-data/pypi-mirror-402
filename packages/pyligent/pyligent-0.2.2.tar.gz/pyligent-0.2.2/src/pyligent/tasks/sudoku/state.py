from typing import Literal, Optional

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.state import StateEngine
from pyligent.tasks.sudoku.grid import Grid

SudokuStateEngineMode = Literal["full", "action"]


class SudokuStateEngine(StateEngine):
    def _reduce_full_mode(self, parent_state: Grid, action: Action) -> Grid:
        if isinstance(action, NodeAction):
            new_state = Grid.from_string(action.text, spec=parent_state.spec)
            new_state._pivots = parent_state.get_pivots_mask()
            return new_state

        if isinstance(action, DoneAction):
            new_state = Grid.from_string(action.answer, spec=parent_state.spec)
            new_state._pivots = parent_state.get_pivots_mask()
            return new_state

        if isinstance(action, BacktrackAction):
            # Backtrack doesn't modify state
            return parent_state

        return parent_state

    def _reduce_action_mode(self, parent_state: Grid, action: Action) -> Grid:
        if isinstance(action, NodeAction):
            row, column, value = map(int, action.text.split())
            new_state = parent_state.copy()
            new_state.set(row, column, value)
            return new_state

        if isinstance(action, DoneAction):
            row, column, value = map(int, action.answer.split())
            new_state = parent_state.copy()
            new_state.set(row, column, value)
            return new_state

        if isinstance(action, BacktrackAction):
            # Backtrack doesn't modify state
            return parent_state

        return parent_state

    def __init__(self, mode: SudokuStateEngineMode = "full") -> None:
        self._mode = mode

        if self._mode == "full":
            self._reduce = self._reduce_full_mode
        else:
            self._reduce = self._reduce_action_mode

    def reduce(self, parent_state: Optional[Grid], action: Action) -> Grid:
        if parent_state is None:
            raise NotImplementedError()

        try:
            return self._reduce(parent_state, action)
        except BaseException:
            # Assume Validator catch all the errors
            pass

        return parent_state
