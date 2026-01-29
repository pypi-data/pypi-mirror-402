import math
from dataclasses import dataclass
from typing import List, Literal, Sequence

from pyligent.core.explorer import Explorer, ExplorerConfig, Frontier, PrefixState

SamplingStrategy = Literal["prefer_nodes", "prefer_children"]
CapacityMode = Literal["linear", "exponential"]


@dataclass(slots=True)
class BaseDendriticExplorerConfig(ExplorerConfig):
    # Transition/scoring params
    sampling_transition_point: float = 2.0
    h: float = 2.0
    alpha_bfs: float = -1.0
    alpha_dfs: float = 1.0
    beta: float = 1.0
    epsilon: float = 1e-6

    # Sampling params
    sampling_nodes: int = 0

    # c_max(i) policy
    capacity_mode: CapacityMode = "exponential"

    def __post_init__(self) -> None:
        if not self.sampling_nodes:
            self.sampling_nodes = self.branching_factor


@dataclass(slots=True)
class DendriticExplorerConfig(BaseDendriticExplorerConfig):
    sampling_strategy: SamplingStrategy = "prefer_nodes"


class DendriticExplorer(Explorer):
    def __init__(self, config: DendriticExplorerConfig):
        super().__init__(config=config)

    @property
    def cfg(self) -> DendriticExplorerConfig:
        # Convenience typed accessor
        return self.config  # type: ignore[return-value]

    def _max_children_for_frontier(self, frontier: Frontier) -> int:
        if self.cfg.capacity_mode == "linear":
            return self.cfg.branching_factor if frontier.depth == 0 else 1
        return self.cfg.branching_factor

    def _sigma(self, N: int) -> float:
        # progress = log_B(N), switch around N ≈ B^s
        B = max(2, int(self.cfg.branching_factor))
        log_b_n = math.log(max(1, N), B)
        x = self.cfg.h * (log_b_n - self.cfg.sampling_transition_point)
        return 1.0 / (1.0 + math.exp(-x))

    def _alpha(self, N: int) -> float:
        sig = self._sigma(N)
        return self.cfg.alpha_bfs + (self.cfg.alpha_dfs - self.cfg.alpha_bfs) * sig

    def _expandable_frontiers(self, state: PrefixState) -> List[Frontier]:
        out: list[Frontier] = []
        for f in state.stack:
            max_children = self._max_children_for_frontier(f)
            if f.children >= max_children:
                continue
            # Also avoid expanding nodes that are already at/over max depth.
            if len(f.context) >= state.max_depth_abs:
                continue
            out.append(f)
        return out

    def _allocate_children_prefer_nodes(
        self,
        frontiers: Sequence[Frontier],
        probs: Sequence[float],
        U: int,
    ) -> List[int]:
        """
        Allocate children using round-robin to prefer coverage across nodes.

        Optimized to batch complete allocation rounds instead of one-by-one distribution.
        Complexity: O(n * max_capacity) instead of O(U * n).
        """
        n = len(frontiers)
        if n == 0 or U <= 0:
            return []

        # Sort indices by probability (descending)
        order = sorted(range(n), key=lambda i: probs[i], reverse=True)

        # Compute remaining capacity for each frontier
        caps = [
            max(0, self._max_children_for_frontier(frontiers[i]) - frontiers[i].children)
            for i in range(n)
        ]

        alloc = [0] * n
        remaining = U

        # Batch round-robin allocation
        while remaining > 0:
            # Identify active nodes (those with remaining capacity)
            active = [i for i in order if alloc[i] < caps[i]]

            if not active:
                break

            num_active = len(active)

            if remaining >= num_active:
                # We can afford at least one complete round across all active nodes
                # Find how many complete rounds we can do (limited by minimum remaining capacity)
                min_remaining_capacity = min(caps[i] - alloc[i] for i in active)
                max_affordable_rounds = remaining // num_active
                rounds = min(max_affordable_rounds, min_remaining_capacity)

                # Allocate 'rounds' children to each active node
                for i in active:
                    alloc[i] += rounds
                    remaining -= rounds
            else:
                # Budget insufficient for complete round; allocate remainder one-by-one
                for i in active[:remaining]:
                    alloc[i] += 1
                remaining = 0

        return alloc

    def _allocate_children_prefer_children(
        self,
        frontiers: Sequence[Frontier],
        probs: Sequence[float],
        U: int,
    ) -> List[int]:
        # Greedy fill: allocate as much as possible to top node, then next.
        order = sorted(range(len(frontiers)), key=lambda i: probs[i], reverse=True)
        caps = [
            self._max_children_for_frontier(frontiers[i]) - frontiers[i].children
            for i in range(len(frontiers))
        ]
        alloc = [0] * len(frontiers)

        remaining = U
        for i in order:
            if remaining <= 0:
                break
            take = min(remaining, caps[i])
            if take > 0:
                alloc[i] = take
                remaining -= take

        return alloc

    def _compute_scores(
        self, state: PrefixState, expandable: list[Frontier]
    ) -> Sequence[float]:
        # Normalized scoring to avoid absolute depth and absolute gap dependence.
        #
        # Depth normalization:
        # - frontier.depth is already relative to the prefix-root (0 at prefix-root).
        # - state.max_depth is an absolute max length (includes prefix length).
        # - prefix_len can be reconstructed since: len(context) = prefix_len + depth.
        #
        # Gap normalization:
        # - use fractional remaining capacity: gap / max_children.
        #
        # log(score_i) = alpha*log(1 + depth/max_extra_depth) + beta*log(1 + gap/max_children + eps)

        # N: total generated nodes in this prefix-tree.
        N = max(1, int(state.discovered_nodes) + 1)
        eps = float(self.cfg.epsilon)
        alpha = self._alpha(N)
        beta = float(self.cfg.beta)

        log_scores: list[float] = []
        for f in expandable:
            max_children = int(self._max_children_for_frontier(f))

            # Remaining expansion capacity for this node
            gap = max(0, max_children - int(f.children))
            gap_scaled = 1.0 + (gap / max(1, max_children)) + eps

            # Reconstruct prefix length and normalize relative depth to known max depth
            prefix_len = max(0, int(len(f.context) - int(f.depth)))
            max_extra_depth = max(1, int(state.max_depth_abs - prefix_len))

            d_rel = max(0, int(f.depth))
            d_scaled = 1.0 + (d_rel / max_extra_depth)

            log_scores.append(alpha * math.log(d_scaled) + beta * math.log(gap_scaled))

        return log_scores

    def _select_from_allocated(
        self, state: PrefixState, expandable: list[Frontier], alloc: list[int]
    ) -> List[Frontier]:
        # Remove selected frontiers from stack to avoid duplicates; keep others.
        selected: list[Frontier] = []
        keep: list[Frontier] = []
        alloc_by_id = {id(f): k for f, k in zip(expandable, alloc)}

        for f in state.stack:
            k = alloc_by_id.get(id(f), 0)
            if k > 0:
                f.requested_children = k
                selected.append(f)
            else:
                keep.append(f)

        state.stack = keep
        return selected

    def _sample_frontiers(self, state: PrefixState) -> List[Frontier]:
        expandable = self._expandable_frontiers(state)
        if not expandable:
            return []

        log_scores = self._compute_scores(state, expandable)

        U = max(1, int(self.cfg.sampling_nodes))
        if self.cfg.sampling_strategy == "prefer_children":
            alloc = self._allocate_children_prefer_children(expandable, log_scores, U)
        else:
            alloc = self._allocate_children_prefer_nodes(expandable, log_scores, U)

        return self._select_from_allocated(state, expandable, alloc)
