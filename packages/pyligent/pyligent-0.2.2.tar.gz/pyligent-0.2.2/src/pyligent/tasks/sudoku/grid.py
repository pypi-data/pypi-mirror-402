from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pyligent.tasks.sudoku.spec import SudokuSpec


def _box_index(spec: SudokuSpec, row: int, col: int) -> int:
    """Map (row, col) -> box index for arbitrary box shapes."""
    boxes_per_row = spec.size // spec.box_cols
    return (row // spec.box_rows) * boxes_per_row + (col // spec.box_cols)


@dataclass
class Grid:
    """Sudoku grid supporting 4x4, 6x6, and 9x9.

    Internal representation:
      - _data: string of length size*size
      - '0' means empty
      - '1'..'{size}' are filled values
    """

    spec: SudokuSpec = field(default_factory=lambda: SudokuSpec.default_for_size(9))
    _data: str = field(default="", repr=False)

    _row_cache: list[int] = field(init=False, repr=False)
    _col_cache: list[int] = field(init=False, repr=False)
    _box_cache: list[int] = field(init=False, repr=False)

    # Bitmask: 1 bit per cell. Set => pivot (initial clue).
    _pivots: int = field(init=False, repr=False, default=0)

    # Cached solvability (invalidated on mutation).
    _solvable_cache: Optional[bool] = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        self.spec.validate()

        if not self._data:
            self._data = "0" * self.spec.cell_count

        if len(self._data) != self.spec.cell_count:
            raise ValueError(
                f"Grid data must be length {self.spec.cell_count}, got {len(self._data)}"
            )

        allowed = set("0" + "".join(str(i) for i in range(1, self.spec.size + 1)))
        if any(ch not in allowed for ch in self._data):
            raise ValueError(
                f"Grid data contains invalid symbols for size={self.spec.size}: {set(self._data) - allowed}"
            )

        self._row_cache = [0] * self.spec.size
        self._col_cache = [0] * self.spec.size
        self._box_cache = [0] * self.spec.box_count
        self._solvable_cache = None
        self._pivots = 0

        # Build caches + pivots from current data (assumed "initial clues" on construction).
        for idx in range(self.spec.cell_count):
            val = int(self._data[idx])
            if val == 0:
                continue

            self._pivots |= 1 << idx

            row, col = divmod(idx, self.spec.size)
            box = _box_index(self.spec, row, col)
            bit = 1 << val

            # If duplicates exist at construction time, caches will encode them;
            # caller can detect via is_valid().
            self._row_cache[row] |= bit
            self._col_cache[col] |= bit
            self._box_cache[box] |= bit

    # -------------------------
    # Construction helpers
    # -------------------------

    @classmethod
    def empty(cls, spec: SudokuSpec) -> "Grid":
        return cls(spec=spec, _data="0" * spec.cell_count)

    @staticmethod
    def _infer_size_from_string(s: str) -> int:
        # Accept only Nikoli-like flat strings with '.' or '0' for empties.
        stripped = s.strip().replace("\n", "").replace(" ", "")
        n = len(stripped)
        size = int(n**0.5)
        if size * size != n:
            raise ValueError(f"Cannot infer sudoku size from length={n}.")
        if size not in (4, 6, 9):
            raise ValueError(f"Inferred unsupported size={size}. Supported: 4, 6, 9.")
        return size

    @classmethod
    def from_string(cls, s: str, spec: SudokuSpec | None = None) -> "Grid":
        """Parse a Nikoli-like flat string.

        Accepted:
          - '.' or '0' => empty
          - '1'..'{size}' digits
          - Optional whitespace/newlines (will be removed)
        """
        raw = s.strip().replace("\n", "").replace(" ", "")
        if spec is None:
            spec = SudokuSpec.default_for_size(cls._infer_size_from_string(raw))

        allowed = set("." + "0" + "".join(str(i) for i in range(1, spec.size + 1)))
        if len(raw) != spec.cell_count:
            raise ValueError(f"Expected length {spec.cell_count}, got {len(raw)}.")
        if any(ch not in allowed for ch in raw):
            raise ValueError(
                f"Invalid characters for size={spec.size}: {set(raw) - allowed}"
            )

        return cls(spec=spec, _data=raw.replace(".", "0"))

    def to_canonical(self) -> str:
        """Return Nikoli-like canonical (dots for empties)."""
        return self._data.replace("0", ".")

    def to_2d_list(self) -> list[list[int]]:
        n = self.spec.size
        return [[int(self._data[r * n + c]) for c in range(n)] for r in range(n)]

    def to_human_readable(self, empty_char: str = ".") -> str:
        """Return human-readable grid representation with box separators.

        Args:
            empty_char: Character to use for empty cells (default '.')

        Returns:
            Formatted string with grid separators adapted to sudoku variant
        """
        n = self.spec.size
        box_rows = self.spec.box_rows
        box_cols = self.spec.box_cols

        # Calculate separator line width
        # Formula: cells + spaces_between_cells + box_separators
        num_col_separators = (n // box_cols) - 1
        separator_width = n + (n - 1) + (num_col_separators * 2)

        lines = []
        for r in range(n):
            # Insert horizontal separator between box rows
            if r % box_rows == 0 and r != 0:
                lines.append("-" * separator_width)

            row_chars = []
            for c in range(n):
                # Insert vertical separator between box columns
                if c % box_cols == 0 and c != 0:
                    row_chars.append("|")

                val = self.get(r, c)
                row_chars.append(str(val) if val != 0 else empty_char)

            lines.append(" ".join(row_chars))

        return "\n".join(lines)

    # -------------------------
    # Pivots
    # -------------------------

    def is_pivot(self, row: int, col: int) -> bool:
        idx = self._index(row, col)
        return bool(self._pivots & (1 << idx))

    def get_pivots_mask(self) -> int:
        return self._pivots

    # -------------------------
    # Indexing / access
    # -------------------------

    def _index(self, row: int, col: int) -> int:
        n = self.spec.size
        return row * n + col

    def get(self, row: int, col: int) -> int:
        return int(self._data[self._index(row, col)])

    # -------------------------
    # Validations
    # -------------------------

    def is_valid_placement(self, row: int, col: int, val: int) -> bool:
        n = self.spec.size
        if not (0 <= row < n and 0 <= col < n):
            return False
        if not (1 <= val <= n):
            return False
        if self.get(row, col) != 0:
            return False

        bit = 1 << val
        box = _box_index(self.spec, row, col)

        return not (
            (self._row_cache[row] & bit)
            or (self._col_cache[col] & bit)
            or (self._box_cache[box] & bit)
        )

    def is_valid(self) -> bool:
        """Check global validity (no duplicates in row/col/box)."""
        n = self.spec.size
        rows = [0] * n
        cols = [0] * n
        boxes = [0] * self.spec.box_count

        for idx in range(self.spec.cell_count):
            val = int(self._data[idx])
            if val == 0:
                continue
            row, col = divmod(idx, n)
            box = _box_index(self.spec, row, col)
            bit = 1 << val
            if (rows[row] & bit) or (cols[col] & bit) or (boxes[box] & bit):
                return False
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit

        return True

    def is_complete(self) -> bool:
        return "0" not in self._data

    def find_empty_cell(self) -> Optional[tuple[int, int]]:
        idx = self._data.find("0")
        if idx == -1:
            return None
        return divmod(idx, self.spec.size)

    # -------------------------
    # Mutation
    # -------------------------

    def set(self, row: int, col: int, val: int) -> bool:
        n = self.spec.size
        if not (0 <= row < n and 0 <= col < n):
            return False
        if not (0 <= val <= n):
            return False

        idx = self._index(row, col)
        old_val = int(self._data[idx])

        # Any mutation invalidates cached solvability.
        self._solvable_cache = None

        box = _box_index(self.spec, row, col)

        # Clear cell
        if val == 0:
            if old_val != 0:
                bit_old = 1 << old_val
                self._row_cache[row] &= ~bit_old
                self._col_cache[col] &= ~bit_old
                self._box_cache[box] &= ~bit_old
            self._data = self._data[:idx] + "0" + self._data[idx + 1 :]
            return True

        # Place value
        if old_val == 0:
            if not self.is_valid_placement(row, col, val):
                return False
        else:
            # Replace existing value: temporarily remove old from caches and re-check.
            bit_old = 1 << old_val
            self._row_cache[row] &= ~bit_old
            self._col_cache[col] &= ~bit_old
            self._box_cache[box] &= ~bit_old

            bit_new = 1 << val
            conflict = (
                (self._row_cache[row] & bit_new)
                or (self._col_cache[col] & bit_new)
                or (self._box_cache[box] & bit_new)
            )
            if conflict:
                # restore old
                self._row_cache[row] |= bit_old
                self._col_cache[col] |= bit_old
                self._box_cache[box] |= bit_old
                return False

        self._data = self._data[:idx] + str(val) + self._data[idx + 1 :]
        bit_new = 1 << val
        self._row_cache[row] |= bit_new
        self._col_cache[col] |= bit_new
        self._box_cache[box] |= bit_new
        return True

    def copy(self) -> "Grid":
        new_grid = Grid(spec=self.spec, _data=self._data)
        new_grid._pivots = self._pivots
        return new_grid

    # -------------------------
    # Step validation (training)
    # -------------------------

    def validate_next_step(self, next_grid: "Grid") -> bool:
        """Valid next step = fill exactly one empty cell, keep all clues unchanged."""
        if not isinstance(next_grid, Grid):
            return False
        if next_grid.spec != self.spec:
            return False

        changes: list[tuple[int, int]] = []
        for idx in range(self.spec.cell_count):
            if self._data[idx] == next_grid._data[idx]:
                continue

            old_val = int(self._data[idx])
            new_val = int(next_grid._data[idx])

            if old_val != 0:
                return False
            if new_val == 0:
                return False

            changes.append((idx, new_val))

        if len(changes) != 1:
            return False

        idx, val = changes[0]
        row, col = divmod(idx, self.spec.size)
        return self.is_valid_placement(row, col, val)

    def verify_pivots_preserved(
        self, other: "Grid"
    ) -> tuple[bool, Optional[tuple[int, int]]]:
        if not isinstance(other, Grid):
            return (False, None)
        if other.spec != self.spec:
            return (False, None)

        for idx in range(self.spec.cell_count):
            if self._pivots & (1 << idx):
                if self._data[idx] != other._data[idx]:
                    row, col = divmod(idx, self.spec.size)
                    return (False, (row, col))
        return (True, None)

    # -------------------------
    # Solvability (used in generation)
    # -------------------------

    def is_solvable(self) -> bool:
        if self._solvable_cache is not None:
            return self._solvable_cache
        if not self.is_valid():
            self._solvable_cache = False
            return False
        self._solvable_cache = self._check_solvable(self.copy())
        return self._solvable_cache

    def _check_solvable(self, grid: "Grid") -> bool:
        empty = grid.find_empty_cell()
        if empty is None:
            return True

        row, col = empty
        for val in range(1, grid.spec.size + 1):
            if grid.is_valid_placement(row, col, val):
                grid.set(row, col, val)
                if self._check_solvable(grid):
                    return True
                grid.set(row, col, 0)
        return False

    def __str__(self) -> str:
        return self.to_human_readable()

    def __repr__(self) -> str:
        return f"Grid(spec={self.spec}, data='{self._data}')"


@dataclass
class GridGeneration(Grid):
    """Grid with candidate enumeration for puzzle generation."""

    def get_candidates(self, row: int, col: int) -> list[int]:
        if self.get(row, col) != 0:
            return []

        box = _box_index(self.spec, row, col)
        used = self._row_cache[row] | self._col_cache[col] | self._box_cache[box]
        return [v for v in range(1, self.spec.size + 1) if not (used & (1 << v))]

    @classmethod
    def from_grid(cls, grid: Grid) -> "GridGeneration":
        return cls(spec=grid.spec, _data=grid._data)

    def to_grid(self) -> Grid:
        g = Grid(spec=self.spec, _data=self._data)
        g._pivots = self._pivots
        return g
