from pathlib import Path
from typing import Optional

import orjson
import yaml
from loguru import logger

from pyligent.core.action import DoneAction, NodeAction
from pyligent.core.path import GoldPath, Node
from pyligent.tasks.sudoku.grid import Grid
from pyligent.tasks.sudoku.spec import SudokuSpec


class SudokuAdapter:
    """Adapter for loading Sudoku datasets and converting to golden paths.

    Dataset structure:
    - puzzles.jsonl: Contains puzzle definitions
    - chains.jsonl: Contains solution step chains
    - index.yaml: Contains metadata

    Attributes:
        dataset_path: Path to dataset directory
        metadata: Dataset metadata from index.yaml
        num_puzzles: Total number of puzzles in dataset
    """

    def __init__(self, dataset_path: str | Path) -> None:
        """Initialize adapter with dataset path.

        Args:
            dataset_path: Path to dataset directory containing puzzles.jsonl,
                chains.jsonl, and index.yaml

        Raises:
            FileNotFoundError: If dataset path or required files don't exist
            ValueError: If dataset structure is invalid
        """
        self.dataset_path = Path(dataset_path)

        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")

        if not self.dataset_path.is_dir():
            raise ValueError(f"Dataset path must be a directory: {self.dataset_path}")

        # Verify required files exist
        self.puzzles_path = self.dataset_path / "puzzles.jsonl"
        self.chains_path = self.dataset_path / "chains.jsonl"
        self.index_path = self.dataset_path / "index.yaml"

        if not self.puzzles_path.exists():
            raise FileNotFoundError(f"Missing puzzles.jsonl in {self.dataset_path}")

        if not self.chains_path.exists():
            raise FileNotFoundError(f"Missing chains.jsonl in {self.dataset_path}")

        if not self.index_path.exists():
            raise FileNotFoundError(f"Missing index.yaml in {self.dataset_path}")

        # Load metadata
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.metadata = yaml.safe_load(f)

        self.num_puzzles = self.metadata.get("total_examples", 0)

        # Choose sudoku spec from dataset metadata
        grid_meta = (self.metadata or {}).get("grid", {}) or {}
        size = int(grid_meta.get("size", 9))
        box_rows = grid_meta.get("box_rows", None)
        box_cols = grid_meta.get("box_cols", None)
        self.spec = SudokuSpec.from_grid_config(
            size=size, box_rows=box_rows, box_cols=box_cols
        )

        logger.info(
            f"Loaded Sudoku adapter: {self.num_puzzles} puzzles from {self.dataset_path}"
        )

    def _read_chains(self) -> list[dict]:
        """Read solution chains from JSONL file.

        Returns:
            List of chain dictionaries with structure:
            {
                "id": str,
                "initial_board": str (Nikoli100 format),
                "actions": list[dict],
                "num_steps": int
            }
        """
        chains = []
        with open(self.chains_path, "rb") as f:
            for line in f:
                if line.strip():
                    chains.append(orjson.loads(line))
        return chains

    def load_golden_paths(
        self,
        size: Optional[int] = None,
        difficulty: Optional[str] = None,
        start_idx: int = 0,
    ) -> list[GoldPath]:
        """Load golden solution paths from dataset.

        Args:
            size: Number of paths to load. If None, loads all available paths
            difficulty: Filter by difficulty level (e.g., "easy", "medium", "hard", "expert").
                If None, loads all difficulties
            start_idx: Starting index for loading (for pagination/splitting datasets)

        Returns:
            List of GoldPath objects representing solution chains

        """
        chains = self._read_chains()

        # Filter by difficulty if specified
        if difficulty is not None:
            chains = [
                chain for chain in chains if chain["id"].startswith(f"{difficulty}_")
            ]
            logger.info(f"Filtered to {len(chains)} {difficulty} puzzles")

        # Apply pagination
        if start_idx > 0:
            chains = chains[start_idx:]

        if size is not None:
            chains = chains[:size]

        logger.info(f"Loading {len(chains)} golden paths...")

        golden_paths = []
        for chain_data in chains:
            gold_path = self._chain_to_gold_path(chain_data)
            golden_paths.append(gold_path)

        logger.success(f"Loaded {len(golden_paths)} golden paths")
        return golden_paths

    def _chain_to_gold_path(self, chain_data: dict) -> GoldPath:
        """Convert chain data to GoldPath object.

        Args:
            chain_data: Dictionary containing:
                - id: puzzle identifier
                - initial_board: starting puzzle state (Nikoli100)
                - actions: list of solution steps
                - num_steps: total steps in solution

        Returns:
            GoldPath with nodes representing each step of the solution
        """
        chain_data["id"]
        initial_board = chain_data["initial_board"]
        actions = chain_data["actions"]

        # Create root node with initial puzzle state
        initial_grid = Grid.from_string(initial_board, spec=self.spec)
        root_node = Node(
            parent=None, action=NodeAction(0, initial_board), state=initial_grid
        )

        nodes = [root_node]

        # Build intermediate nodes from action chain
        for step_idx, action_data in enumerate(actions[:-1]):  # All but last
            parent = nodes[-1]
            resulting_board = action_data["resulting_board"]

            # Create action with resulting board state
            action = NodeAction(step_idx + 1, resulting_board)

            # Parse grid state
            grid_state = Grid.from_string(resulting_board, spec=self.spec)

            # Create node
            node = Node(parent=parent, action=action, state=grid_state)
            nodes.append(node)

        # Handle final action (DoneAction)
        if len(actions) > 0:
            parent = nodes[-1]
            final_action_data = actions[-1]
            final_board = final_action_data["resulting_board"]

            # Final action is DoneAction
            done_action = DoneAction(final_board)

            # Parse final grid state
            final_grid = Grid.from_string(final_board, spec=self.spec)

            # Create final node
            done_node = Node(parent=parent, action=done_action, state=final_grid)
            nodes.append(done_node)

        return GoldPath(nodes)

    def load_puzzles_only(
        self,
        size: Optional[int] = None,
        difficulty: Optional[str] = None,
        start_idx: int = 0,
    ) -> list[Grid]:
        """Load only puzzle grids without solution chains.

        Useful for evaluation/testing where you don't need the golden path.

        Args:
            size: Number of puzzles to load. If None, loads all
            difficulty: Filter by difficulty level
            start_idx: Starting index for pagination

        Returns:
            List of Grid objects representing puzzles
        """
        puzzles = []
        with open(self.puzzles_path, "rb") as f:
            for line in f:
                if line.strip():
                    puzzles.append(orjson.loads(line))

        # Filter by difficulty if specified
        if difficulty is not None:
            puzzles = [p for p in puzzles if p["difficulty"] == difficulty]

        # Apply pagination
        if start_idx > 0:
            puzzles = puzzles[start_idx:]

        if size is not None:
            puzzles = puzzles[:size]

        logger.info(f"Loading {len(puzzles)} puzzle grids...")

        grids = []
        for puzzle_data in puzzles:
            grid = Grid.from_string(puzzle_data["puzzle"], spec=self.spec)
            grids.append(grid)

        return grids
