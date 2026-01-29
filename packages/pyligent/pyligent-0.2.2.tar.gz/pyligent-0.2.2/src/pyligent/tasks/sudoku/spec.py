from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SudokuSpec:
    """Describes a Sudoku variant (size and box shape).

    Examples:
        - 4x4: size=4, box_rows=2, box_cols=2
        - 6x6: size=6, box_rows=2, box_cols=3
        - 9x9: size=9, box_rows=3, box_cols=3
    """

    size: int
    box_rows: int
    box_cols: int

    @property
    def cell_count(self) -> int:
        return self.size * self.size

    @property
    def box_count(self) -> int:
        # For classic Sudoku variants, this equals size (e.g., 9 boxes in 9x9).
        return (self.size // self.box_rows) * (self.size // self.box_cols)

    def validate(self) -> None:
        if self.size not in (4, 6, 9):
            raise ValueError(f"Unsupported sudoku size: {self.size}. Supported: 4, 6, 9.")
        if self.size % self.box_rows != 0 or self.size % self.box_cols != 0:
            raise ValueError(
                f"Invalid box shape {self.box_rows}x{self.box_cols} for size {self.size}."
            )
        if self.box_rows * self.box_cols != self.size:
            # Ensures each box contains exactly {1..size}.
            raise ValueError(
                f"Box area must equal size. Got {self.box_rows}*{self.box_cols} != {self.size}."
            )

    @staticmethod
    def default_for_size(size: int) -> "SudokuSpec":
        mapping: dict[int, tuple[int, int]] = {
            4: (2, 2),
            6: (2, 3),
            9: (3, 3),
        }
        if size not in mapping:
            raise ValueError(f"Unsupported size: {size}. Supported: {sorted(mapping)}")
        r, c = mapping[size]
        spec = SudokuSpec(size=size, box_rows=r, box_cols=c)
        spec.validate()
        return spec

    @staticmethod
    def from_grid_config(
        size: int, box_rows: int | None, box_cols: int | None
    ) -> "SudokuSpec":
        if box_rows is None or box_cols is None:
            return SudokuSpec.default_for_size(size)
        spec = SudokuSpec(size=size, box_rows=int(box_rows), box_cols=int(box_cols))
        spec.validate()
        return spec
