from dataclasses import dataclass
from typing import List

from pyligent.core.explorer import Explorer, ExplorerConfig, Frontier, PrefixState


@dataclass(slots=True)
class LinearExplorerConfig(ExplorerConfig):
    """
    Pure linear exploration:
    - root: up to B children (B branches)
    - non-root: only 1 child (a single chain per branch)
    """

    # No extra params for now; kept as a separate config for clarity/extension.
    pass


class LinearExplorer(Explorer):
    """
    Linear explorer:
    - Expand the root by generating all B branches in one step.
    - Then, in each iteration, advance multiple branches in parallel by taking up to B frontiers.
    """

    def __init__(self, config: LinearExplorerConfig):
        super().__init__(config=config)

    def _max_children_for_frontier(self, frontier: Frontier) -> int:
        # Root splits into B branches, then linear chain thereafter.
        return self.config.branching_factor if frontier.depth == 0 else 1

    def _sample_frontiers(self, state: PrefixState) -> List[Frontier]:
        if not state.stack:
            return []

        # If the prefix root is still expandable, expand it greedily to spawn all branches.
        # (root is represented by depth == 0 frontier created in _initialize_prefix_states)
        root = None
        for f in reversed(state.stack):
            if f.depth == 0:
                root = f
                break

        if root is not None and root.children < self.config.branching_factor:
            # Remove root from the stack.
            state.stack.remove(root)

            root.requested_children = self.config.branching_factor - root.children
            return [root]

        # Otherwise: advance multiple branches in parallel by sampling up to B frontiers.
        # Using LIFO keeps behavior closer to DFS but still parallelizes across branches.
        k = min(len(state.stack), self.config.branching_factor)
        selected: list[Frontier] = []
        for _ in range(k):
            f = state.stack.pop()
            f.requested_children = 1
            selected.append(f)
        return selected
