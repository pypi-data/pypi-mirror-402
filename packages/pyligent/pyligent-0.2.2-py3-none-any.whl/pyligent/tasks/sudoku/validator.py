from typing import Optional

from pyligent.core import Validator
from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.path import PathContext
from pyligent.core.validator import HandlerResult
from pyligent.tasks.sudoku.grid import Grid


class SudokuValidator(Validator[Grid]):
    """Validates Sudoku puzzle-solving actions with cached validation.

    Enforces:
    - Grid format correctness and Sudoku constraints
    - Single-step progression (exactly one cell filled per action)
    - Backtracking only when current grid is unsolvable
    - Completion check for DoneAction
    """

    def __init__(self) -> None:
        super().__init__([self._sudoku_rules_handler])
        self._valid_grids: set[str] = set()
        self._solvable_cache: dict[str, bool] = {}

    def _sudoku_rules_handler(
        self, action: Action, context: PathContext[Grid]
    ) -> HandlerResult:
        """Validate Sudoku-specific rules for each action type."""

        # Validate previous state exists
        prev_grid: Optional[Grid] = context.last_node.state
        if prev_grid is None:
            return HandlerResult(False, "Previous node has no state")

        # Handle BacktrackAction
        if isinstance(action, BacktrackAction):
            return HandlerResult(
                False, "Decided to prohibit backtracks during training"
            )  #
            return self._validate_backtrack(prev_grid, action, context)

        # Parse and validate new grid
        try:
            new_grid = Grid.from_string(action.text, spec=prev_grid.spec)
        except (ValueError, Exception) as e:
            return HandlerResult(False, f"Invalid grid format: {str(e)[:100]}")

        new_grid_hash = new_grid.to_canonical()

        # Verify pivots (initial clues) were not modified
        is_preserved, modified_cell = prev_grid.verify_pivots_preserved(new_grid)
        if not is_preserved:
            if modified_cell:
                row, col = modified_cell
                return HandlerResult(
                    False, f"Pivot violation: Initial clue at ({row},{col}) was modified"
                )
            return HandlerResult(False, "Pivot violation: Initial clues were modified")

        # Check Sudoku constraint validity
        if new_grid_hash not in self._valid_grids:
            if not new_grid.is_valid():
                return HandlerResult(False, "Sudoku constraints violated")
            self._valid_grids.add(new_grid_hash)

        # Validate single-step progression
        if not prev_grid.validate_next_step(new_grid):
            return HandlerResult(
                False, "Invalid step: must fill exactly one empty cell with valid value"
            )

        # Handle DoneAction
        if isinstance(action, DoneAction):
            if not new_grid.is_complete():
                return HandlerResult(False, "Puzzle incomplete: empty cells remain")
            return HandlerResult(True, "Puzzle solved!")

        # =Handle NodeAction
        if isinstance(action, NodeAction):
            # Valid intermediate step - no need to check solvability
            return HandlerResult(True)

        # Unreachable with current action types
        return HandlerResult(False, f"Unknown action type: {type(action).__name__}")

    def _validate_backtrack(
        self, prev_grid: Grid, action: BacktrackAction, context: PathContext[Grid]
    ) -> HandlerResult:
        """Validate backtrack action with cached solvability checks.

        Backtracking is only valid if the previous grid is unsolvable.
        """
        prev_grid_hash = prev_grid.to_canonical()

        # Check if previous grid is solvable (with caching)
        if prev_grid_hash in self._solvable_cache:
            is_solvable = self._solvable_cache[prev_grid_hash]
        else:
            is_solvable = prev_grid.is_solvable()
            self._solvable_cache[prev_grid_hash] = is_solvable

        # Reject backtrack if current state is still solvable
        if is_solvable:
            return HandlerResult(
                False, "No reason to backtrack: current grid is solvable"
            )

        # Validate backtrack target exists (base validator already checks this)
        backtracked_grid: Optional[Grid] = context[action.target_id].state
        if backtracked_grid is None:
            return HandlerResult(False, "Backtrack target has no state")

        # Accept backtrack - don't check target solvability
        # (let the agent explore from that point)
        return HandlerResult(True, "Backtracking from unsolvable state")
