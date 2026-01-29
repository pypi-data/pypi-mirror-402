from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from pyligent.core.explorer import Frontier, PrefixState

# Assuming DendriticExplorer and its config are in the local scope or imported
# based on the provided code snippet.
from pyligent.core.explorers.dendritic_explorer import (
    BaseDendriticExplorerConfig,
    DendriticExplorer,
)


@dataclass(slots=True)
class SamplingExplorerConfig(BaseDendriticExplorerConfig):
    """
    Configuration for SamplingExplorer.

    Adds parameters specific to stochastic sampling.
    """

    # Temperature for softmax. Higher values -> more uniform probabilities.
    # Lower values -> sharper peaks (approximating argmax).
    temperature: float = 1.0

    # Random seed for reproducibility.
    seed: Optional[int] = 42069


class SamplingExplorer(DendriticExplorer):
    """
    A dendritic explorer that selects frontiers to expand via stochastic sampling.

    Instead of deterministic allocation strategies (prefer_nodes/children),
    this explorer converts scores to probabilities via softmax and samples
    nodes to expand using a weighted random choice.
    """

    def __init__(self, config: SamplingExplorerConfig):
        super().__init__(config=config)  # ty:ignore[invalid-argument-type]
        self._rng = np.random.default_rng(config.seed)

    @property
    def cfg(self) -> SamplingExplorerConfig:
        return self.config  # type: ignore[return-value]

    def _softmax(
        self, log_scores: Sequence[float | int], temperature: float
    ) -> np.ndarray:
        """
        Compute stable softmax probabilities from log scores.
        """
        if not log_scores:
            return np.array([])

        # Divide by temperature first
        # Handle small temperature to avoid division by zero/overflow
        t = max(1e-4, temperature)
        scores = np.array(log_scores) / t

        # Numerical stability: subtract max
        scores_shifted = scores - np.max(scores)
        exp_scores = np.exp(scores_shifted)

        return exp_scores / np.sum(exp_scores)

    def _sample_allocations(
        self, frontiers: List[Frontier], probs: np.ndarray, total_budget: int
    ) -> List[int]:
        """
        Sample allocation counts for frontiers based on probabilities.

        This handles the logic of ensuring we don't allocate more than
        the remaining capacity of a node.
        """
        n = len(frontiers)
        allocations = [0] * n
        remaining_budget = total_budget

        # Calculate capacities once
        capacities = [
            max(0, self._max_children_for_frontier(f) - f.children) for f in frontiers
        ]

        # Working copy of probabilities that we can mask out
        current_probs = probs.copy()

        # We sample iteratively because some nodes might hit their capacity limits.
        # When a node hits capacity, we zero out its probability and re-normalize.
        while remaining_budget > 0 and np.any(current_probs > 0):
            # Normalize current probabilities
            sum_probs = np.sum(current_probs)
            if sum_probs <= 1e-9:
                break
            normalized_probs = current_probs / sum_probs

            # Efficiently sample a batch of items
            # We sample 'remaining_budget' items, but we might need to discard some
            # if they hit capacity limits, so this is an optimistic batch.
            # In the worst case (many caps hit), this falls back to iterative re-sampling.
            chosen_indices = self._rng.choice(
                n, size=remaining_budget, p=normalized_probs, replace=True
            )

            # Tally up counts from this batch
            counts = np.bincount(chosen_indices, minlength=n)

            # Apply counts respecting capacities
            made_progress = False
            for idx, count in enumerate(counts):
                if count == 0:
                    continue

                current_alloc = allocations[idx]
                cap = capacities[idx]
                space_left = cap - current_alloc

                if space_left <= 0:
                    # This node is already full, shouldn't have been sampled
                    # (logic below ensures prob is 0, but safety check)
                    current_probs[idx] = 0.0
                    continue

                # Take as many as we can up to the sampled count
                to_add = min(count, space_left)
                allocations[idx] += to_add
                remaining_budget -= to_add
                made_progress = True

                # If we filled it up, remove from future sampling
                if allocations[idx] >= cap:
                    current_probs[idx] = 0.0

            # If we didn't add anything despite having budget and probs,
            # it means we are stuck (shouldn't happen with correct logic), break to avoid infinite loop
            if not made_progress:
                break

        return allocations

    def _sample_frontiers(self, state: PrefixState) -> List[Frontier]:
        expandable = self._expandable_frontiers(state)
        if not expandable:
            return []

        # 1. Compute scores (using the logic from DendriticExplorer)
        log_scores = self._compute_scores(state, expandable)

        # 2. Convert to probabilities via softmax
        probs = self._softmax(log_scores, self.cfg.temperature)

        # 3. Determine sampling budget
        U = max(1, int(self.cfg.sampling_nodes))

        # 4. Sample allocations based on probabilities and capacity constraints
        alloc = self._sample_allocations(expandable, probs, U)

        # 5. Select and return frontiers based on allocations
        # (Reusing _select_from_allocated from parent class)
        return self._select_from_allocated(state, expandable, alloc)
