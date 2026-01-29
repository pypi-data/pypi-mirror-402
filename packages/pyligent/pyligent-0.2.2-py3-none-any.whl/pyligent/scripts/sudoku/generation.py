import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, TypedDict

import numpy as np
import orjson
import yaml
from loguru import logger

from pyligent.common.utils.fs import remove_dir
from pyligent.common.utils.logger import setup_logging
from pyligent.tasks.sudoku.grid import Grid, GridGeneration
from pyligent.tasks.sudoku.spec import SudokuSpec


@dataclass
class GridConfig:
    """Sudoku grid configuration for generation."""

    size: int = 9
    box_rows: Optional[int] = None
    box_cols: Optional[int] = None

    def to_spec(self) -> SudokuSpec:
        return SudokuSpec.from_grid_config(
            size=self.size,
            box_rows=self.box_rows,
            box_cols=self.box_cols,
        )


@dataclass
class DatasetConfig:
    """Configuration for dataset generation."""

    dataset_name: str
    num_examples: dict[str, int]  # difficulty -> count
    min_clues: dict[str, int]  # difficulty -> min clues
    random_seed: int
    require_unique: bool
    solutions_limit: int
    save_path: Path
    force: bool

    # NEW: sudoku type control (4/6/9 + box shape)
    grid: GridConfig = field(default_factory=GridConfig)

    # Derived (not set from YAML directly)
    spec: SudokuSpec = field(init=False, repr=False)

    def __post_init__(self):
        self.spec = self.grid.to_spec()

        self.save_path = Path(self.save_path) / self.dataset_name

        if self.save_path.exists():
            if self.force:
                logger.warning(
                    f"Existing dataset on {self.save_path.as_posix()} will be removed!"
                )
                remove_dir(self.save_path)
                self.save_path.mkdir(parents=True)
            else:
                raise RuntimeError(
                    f"Found existing dataset on {self.save_path.as_posix()}!"
                )

    @classmethod
    def from_yaml(cls, path: str) -> "DatasetConfig":
        """Load configuration from YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        grid_cfg = config.pop("grid", {}) or {}
        config["grid"] = GridConfig(**grid_cfg)
        return cls(**config)

    def to_dict(self) -> dict:
        """Convert to dictionary (safe for YAML)."""
        result = asdict(self)
        result["save_path"] = self.save_path.as_posix()
        # Keep spec out of config payload
        result.pop("spec", None)
        return result


class SudokuGeneratorSolver:
    """Solver with chain tracking for dataset generation."""

    def __init__(self, limit: int = 2):
        self.solution_count = 0
        self.limit = limit

    def solve_with_chain(
        self, grid: GridGeneration
    ) -> tuple[bool, list[tuple[int, int, int, str]]]:
        """Solve puzzle and record the solution chain.

        Returns:
            Tuple of (success, chain) where chain is list of
            (row, col, value, resulting_grid_nikoli100_string)
        """
        chain = []
        success = self._solve_recursive(grid, chain)
        return success, chain

    def _solve_recursive(
        self, grid: GridGeneration, chain: list[tuple[int, int, int, str]]
    ) -> bool:
        """Recursively solve with chain tracking."""
        empty = grid.find_empty_cell()
        if empty is None:
            return True

        row, col = empty
        candidates = grid.get_candidates(row, col)

        for val in candidates:
            if grid.set(row, col, val):
                # Record action and resulting state in Nikoli100 format
                chain.append((row, col, val, grid.to_canonical()))

                if self._solve_recursive(grid, chain):
                    return True

                # Backtrack
                grid.set(row, col, 0)
                chain.pop()

        return False

    def count_solutions(self, grid: Grid, limit: Optional[int] = None) -> int:
        """Count number of solutions (up to limit)."""
        self.solution_count = 0
        self.limit = limit if limit is not None else self.limit
        self._count_recursive(grid.copy())
        return self.solution_count

    def _count_recursive(self, grid: Grid) -> None:
        """Recursively count solutions."""
        if self.limit > 0 and self.solution_count >= self.limit:
            return

        empty = grid.find_empty_cell()
        if empty is None:
            self.solution_count += 1
            return

        row, col = empty
        # Use GridGeneration for candidates
        grid_gen = GridGeneration.from_grid(grid)
        candidates = grid_gen.get_candidates(row, col)

        for val in candidates:
            if grid.set(row, col, val):
                self._count_recursive(grid)
                grid.set(row, col, 0)
                if self.solution_count >= self.limit:
                    return


class SudokuGenerator:
    """Generate Sudoku puzzles with configurable difficulty and grid size."""

    def __init__(self, spec: SudokuSpec, random_seed: Optional[int] = None):
        self.spec = spec
        self._rng = np.random.default_rng(seed=random_seed)
        self.seed = random_seed
        self.solver = SudokuGeneratorSolver()

    def generate_solution(self) -> GridGeneration:
        """Generate a complete valid Sudoku solution."""
        grid = GridGeneration(spec=self.spec)  # CHANGED
        self._fill_grid(grid)
        return grid

    def _fill_grid(self, grid: GridGeneration) -> bool:
        """Fill grid using backtracking with randomization."""
        empty = grid.find_empty_cell()
        if empty is None:
            return True

        row, col = empty
        candidates = grid.get_candidates(row, col)
        self._rng.shuffle(candidates)

        for val in candidates:
            if grid.set(row, col, val):
                if self._fill_grid(grid):
                    return True
                grid.set(row, col, 0)

        return False

    def generate_puzzle(
        self, min_clues: int = 30, require_unique: bool = True
    ) -> tuple[Grid, Grid]:
        """Generate puzzle by removing clues from solution."""
        solution = self.generate_solution()
        puzzle = solution.to_grid()

        n = self.spec.size
        positions = [(r, c) for r in range(n) for c in range(n)]  # CHANGED
        self._rng.shuffle(positions)

        clues = n * n  # CHANGED
        for row, col in positions:
            if clues <= min_clues:
                break

            backup = puzzle.get(row, col)
            puzzle.set(row, col, 0)

            if require_unique:
                sol_count = self.solver.count_solutions(puzzle)
                if sol_count != 1:
                    puzzle.set(row, col, backup)
                else:
                    clues -= 1
            else:
                clues -= 1

        return puzzle, solution.to_grid()


class JSONLDatasetWriter:
    """Write dataset in human-readable JSONL format using orjson for performance.

    JSONL (JSON Lines) format: one JSON object per line.
    Uses orjson for fast serialization/deserialization (2-3x faster than json).
    """

    @staticmethod
    def write_puzzles(path: Path, puzzles: list[dict]) -> None:
        """Write puzzles to JSONL file using orjson.

        Each line is a JSON object with:
        - id: puzzle identifier
        - puzzle: 81-character string (Nikoli100 format)
        - solution: 81-character string
        - difficulty: string (easy/medium/hard/expert)
        - num_clues: number of given clues
        """
        with open(path, "wb") as f:  # orjson writes bytes
            for puzzle in puzzles:
                # Add num_clues for convenience
                num_clues = sum(1 for c in puzzle["puzzle"] if c != ".")
                puzzle_entry = {
                    "id": puzzle["id"],
                    "puzzle": puzzle["puzzle"],
                    "solution": puzzle["solution"],
                    "difficulty": puzzle["difficulty"],
                    "num_clues": num_clues,
                }
                # orjson.dumps returns bytes, append newline
                f.write(orjson.dumps(puzzle_entry) + b"\n")

        logger.info(f"Written {len(puzzles)} puzzles to {path}")

    @staticmethod
    def write_chains(path: Path, chains: list[dict]) -> None:
        """Write solution chains to JSONL file using orjson.

        Each line is a JSON object with:
        - id: puzzle identifier
        - initial_board: 81-character string
        - actions: list of action objects
            - grid_format: [row, col, value]
            - string_format: [index, value]
            - resulting_board: 81-character string
        - num_steps: number of actions
        """
        with open(path, "wb") as f:  # orjson writes bytes
            for chain in chains:
                chain_entry = {
                    "id": chain["id"],
                    "initial_board": chain["initial_board"],
                    "actions": chain["actions"],
                    "num_steps": len(chain["actions"]),
                }
                f.write(orjson.dumps(chain_entry) + b"\n")

        logger.info(f"Written {len(chains)} chains to {path}")

    @staticmethod
    def read_puzzles(path: Path) -> list[dict]:
        """Read puzzles from JSONL file using orjson."""
        puzzles = []
        with open(path, "rb") as f:  # orjson reads bytes
            for line in f:
                if line.strip():  # Skip empty lines
                    puzzles.append(orjson.loads(line))

        logger.info(f"Read {len(puzzles)} puzzles from {path}")
        return puzzles

    @staticmethod
    def read_chains(path: Path) -> list[dict]:
        """Read chains from JSONL file using orjson."""
        chains = []
        with open(path, "rb") as f:  # orjson reads bytes
            for line in f:
                if line.strip():  # Skip empty lines
                    chains.append(orjson.loads(line))

        logger.info(f"Read {len(chains)} chains from {path}")
        return chains


class Statistics(TypedDict):
    generated: int
    rejected: int
    by_difficulty: dict


def generate_dataset(config: DatasetConfig) -> None:
    """Generate complete Sudoku dataset from configuration."""
    logger.info(f"Starting dataset generation: {config.dataset_name}")
    logger.info(f"Random seed: {config.random_seed}")
    logger.info(f"Unique solutions only: {config.require_unique}")

    # Create output directory
    logger.info(f"Output directory: {config.save_path.as_posix()}")

    # Initialize generator
    generator = SudokuGenerator(spec=config.spec, random_seed=config.random_seed)
    solver = SudokuGeneratorSolver(limit=config.solutions_limit)

    # Storage for all puzzles and chains
    all_puzzles = []
    all_chains = []

    # Statistics
    stats: Statistics = {"generated": 0, "rejected": 0, "by_difficulty": {}}

    # Generate for each difficulty level
    for difficulty, count in config.num_examples.items():
        logger.info(f"Generating {count} {difficulty} puzzles...")

        min_clues = config.min_clues[difficulty]
        difficulty_stats = {"generated": 0, "rejected": 0}

        idx = 0
        attempts = 0
        max_attempts = count * 10  # Safety limit

        while idx < count and attempts < max_attempts:
            attempts += 1

            # Generate puzzle
            puzzle, solution = generator.generate_puzzle(
                min_clues=min_clues, require_unique=config.require_unique
            )

            # Verify
            if config.require_unique:
                sol_count = solver.count_solutions(puzzle)
                if sol_count != 1:
                    difficulty_stats["rejected"] += 1
                    stats["rejected"] += 1
                    continue

            # Generate solution chain
            puzzle_gen = GridGeneration.from_grid(puzzle)
            success, chain_data = solver.solve_with_chain(puzzle_gen)

            if not success:
                logger.warning(f"Failed to solve generated puzzle (attempt {attempts})")
                difficulty_stats["rejected"] += 1
                stats["rejected"] += 1
                continue

            # Create puzzle entry
            puzzle_id = f"{difficulty}_{idx:04d}"
            puzzle_entry = {
                "id": puzzle_id,
                "puzzle": puzzle.to_canonical(),
                "solution": solution.to_canonical(),
                "difficulty": difficulty,
            }
            all_puzzles.append(puzzle_entry)

            # Create chain entry
            chain_actions = []
            for row, col, val, board in chain_data:
                idx_linear = row * config.spec.size + col
                chain_actions.append(
                    {
                        "grid_format": [row, col, val],
                        "string_format": [idx_linear, val],
                        "resulting_board": board,
                    }
                )

            chain_entry = {
                "id": puzzle_id,
                "initial_board": puzzle.to_canonical(),
                "actions": chain_actions,
            }
            all_chains.append(chain_entry)

            idx += 1
            difficulty_stats["generated"] += 1
            stats["generated"] += 1

            if idx % 10 == 0:
                logger.info(f"  Generated {idx}/{count} {difficulty} puzzles")

        stats["by_difficulty"][difficulty] = difficulty_stats
        logger.success(
            f"Completed {difficulty}: {difficulty_stats['generated']} generated, "
            f"{difficulty_stats['rejected']} rejected"
        )

    # Write JSONL files with orjson
    logger.info("Writing dataset files...")
    writer = JSONLDatasetWriter()

    puzzles_path = config.save_path / "puzzles.jsonl"
    chains_path = config.save_path / "chains.jsonl"

    writer.write_puzzles(puzzles_path, all_puzzles)
    writer.write_chains(chains_path, all_chains)

    # Create index file
    logger.info("Creating index file...")
    index_data = {
        "name": config.dataset_name,
        "total_examples": stats["generated"],
        "date_created": datetime.now().isoformat(),
        "format": "jsonl",
        "version": "1.0",
        "serializer": "orjson",
        "grid": {
            "size": config.spec.size,
            "box_rows": config.spec.box_rows,
            "box_cols": config.spec.box_cols,
        },
        "config": config.to_dict(),
        "statistics": stats,
        "files": {
            "puzzles": str(puzzles_path.relative_to(config.save_path.parent)),
            "chains": str(chains_path.relative_to(config.save_path.parent)),
        },
    }

    index_path = config.save_path / "index.yaml"
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index_data, f, default_flow_style=False, sort_keys=False)

    logger.success("Dataset generation complete!")
    logger.info(f"Total puzzles: {stats['generated']}")
    logger.info(f"Total rejected: {stats['rejected']}")
    logger.info(f"Output: {config.save_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Sudoku dataset from YAML configuration"
    )
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="Path to YAML configuration file"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=True,
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logger
    setup_logging(verbose=args.verbose)

    # Load configuration
    try:
        config = DatasetConfig.from_yaml(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    setup_logging(
        verbose=args.verbose,
        log_file=config.save_path / "generation.log",
    )

    # Generate dataset
    try:
        generate_dataset(config)
        return 0
    except Exception as e:
        logger.exception(f"Dataset generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
