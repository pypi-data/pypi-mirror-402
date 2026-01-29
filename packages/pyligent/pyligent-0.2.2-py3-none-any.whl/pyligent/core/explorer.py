import math
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional, Protocol

from loguru import logger

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.dataset import DiligentDatasetItem, DiligentDatasetView
from pyligent.core.helpers.explore_techniques import (
    MAX_ACTIONS_DICT,
    ExploreTechniques,
    MaxActionsFunction,
)
from pyligent.core.path import Node, PathContext
from pyligent.core.solver import Solver
from pyligent.core.state import StateEngine, TextConcatStateEngine
from pyligent.core.validator import Validator

SuccessLeaf = tuple[PathContext, DoneAction]
FailedLeaf = tuple[PathContext, BacktrackAction]
ExploreResult = tuple[list[SuccessLeaf], list[FailedLeaf]]


class BacktrackLogger(Protocol):
    """
    Minimal logger interface needed by Explorer.

    This keeps Explorer independent from any specific logging implementation
    (TrainingRunLogger, PipelineLoggingManager, etc.).
    """

    def log_backtrack_event(
        self,
        *,
        phase: str,
        t: int,
        depth: int,
        path_nodes: list["Node"],
        backtrack_action: "Action",
        raw_path_nodes: Optional[list["Node"]] = None,
    ) -> None: ...


@dataclass(slots=True)
class ExplorationStatistics:
    """Statistics tracking for a single explore() call."""

    start_time: float
    total_nodes_explored: int = 0
    solver_calls: int = 0
    prefixes_completed: int = 0
    total_prefixes: int = 0
    last_logged_percentage: int = 0

    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    def completion_percentage(self) -> int:
        if self.total_prefixes == 0:
            return 0
        return int((self.prefixes_completed / self.total_prefixes) * 100)


@dataclass(slots=True)
class Frontier:
    """A single expandable node inside a prefix-local exploration tree."""

    prefix_idx: int
    context: PathContext
    depth: int = 0
    children: int = 0
    requested_children: int = 1


@dataclass
class PrefixState:
    """Per-prefix exploration state."""

    stack: list[Frontier]
    prefix_gold_node_id: int
    success_path_node_ids: set[int]
    leaves_seen: int
    solutions: list[SuccessLeaf]
    failed: list[FailedLeaf]
    max_depth_abs: int
    discovered_nodes: int
    seen_hashes: set[tuple[int, int]] = field(default_factory=set)
    appearance_counter: int = 0
    is_completed: bool = False


@dataclass(slots=True)
class ExplorerConfig:
    branching_factor: int
    max_depth: int
    leaf_budget_multiplier: float
    max_leaf_capability: Optional[int]
    explore_batch_size: int = 128
    max_actions_strategy: MaxActionsFunction | ExploreTechniques = "linear"
    adaptive_max_depth: bool = True
    adaptive_max_depth_buffer: int = 0
    state_engine: StateEngine = field(default_factory=TextConcatStateEngine)
    always_renumber_node_id: bool = True
    allow_backtracks: bool = False
    deduplication: bool = True
    afterwards_backtrack_target: bool = True

    def get_leaf_budget(self, t: int) -> int:
        computed_budget = max(1, math.ceil(self.leaf_budget_multiplier * t))
        if self.max_leaf_capability is None:
            return computed_budget
        return min(computed_budget, self.max_leaf_capability)

    def get_max_depth(self, prefix_gold_len: Optional[int] = None) -> int:
        if self.adaptive_max_depth and prefix_gold_len:
            return prefix_gold_len + max(0, self.adaptive_max_depth_buffer)
        return self.max_depth

    def get_max_actions_fn(self) -> MaxActionsFunction:
        if callable(self.max_actions_strategy):
            return self.max_actions_strategy
        return MAX_ACTIONS_DICT[self.max_actions_strategy]


class Explorer(ABC):
    """Abstract batched explorer."""

    def __init__(self, config: ExplorerConfig):
        self.config = config
        self._max_actions_fn: MaxActionsFunction = lru_cache(maxsize=256)(
            self.config.get_max_actions_fn()
        )

        self._built: bool = False
        self.training_logger: Optional[BacktrackLogger] = None
        self._current_t: int = 0
        self._stats: Optional[ExplorationStatistics] = None

        self._max_loops = 1000

    @abstractmethod
    def _sample_frontiers(self, state: PrefixState) -> list[Frontier]:
        raise NotImplementedError

    def _max_children_for_frontier(self, frontier: Frontier) -> int:
        return self.config.branching_factor

    def build(self, solver: Solver, validator: Validator) -> None:
        self.solver = solver
        self.validator = validator
        self._built = True

    def set_training_logger(self, training_logger: Optional[BacktrackLogger]) -> None:
        self.training_logger = training_logger

    def is_duplicate(self, state: PrefixState, ctx: PathContext, action: Action) -> bool:
        if not self.config.deduplication:
            return False
        ctx_hash = (ctx.hash_value, action.hash_value)
        if ctx_hash in state.seen_hashes:
            return True
        state.seen_hashes.add(ctx_hash)
        return False

    @staticmethod
    def _lca_node(failed_path: list[Node], success_path_node_ids: set[int]) -> int:
        lca = failed_path[0]
        for node in failed_path:
            if node.identifier in success_path_node_ids:
                lca = node
            else:
                break

        if isinstance(lca.action, NodeAction):
            return lca.action.node_id
        raise RuntimeError("Unreachable")

    def _compute_backtrack_targets(
        self, per_prefix: list[PrefixState], results: list[ExploreResult]
    ) -> list[ExploreResult]:
        for state, (_, failed_leafs) in zip(per_prefix, results):
            for failed_leaf in failed_leafs:
                if failed_leaf[1].target_id >= 0:
                    continue

                target_action_id = self._lca_node(
                    failed_leaf[0].nodes,
                    success_path_node_ids=state.success_path_node_ids,
                )
                failed_leaf[1].target_id = target_action_id
        return results

    def _log_progress(self) -> None:
        if self._stats is None:
            return

        current_percentage = self._stats.completion_percentage()
        if current_percentage >= self._stats.last_logged_percentage + 10:
            self._stats.last_logged_percentage = current_percentage
            logger.debug(
                f"[EXPLORE PROGRESS] t={self._current_t} | "
                f"completion={current_percentage}% "
                f"({self._stats.prefixes_completed}/{self._stats.total_prefixes}) | "
                f"nodes_explored={self._stats.total_nodes_explored} | "
                f"solver_calls={self._stats.solver_calls} | "
                f"elapsed_time={self._stats.elapsed_time():.2f}s"
            )

    def explore(
        self, *, valid_paths: list[DiligentDatasetItem], t: int
    ) -> list[ExploreResult]:
        if not self._built:
            logger.error("Build is required! (call .build(...))")
            raise RuntimeError("Build is required! (call .build(...))")

        self._current_t = t
        leaf_cap = self.config.get_leaf_budget(t)
        total_prefixes = len(valid_paths)
        logger.debug(f"[EXPLORE] t={t} leaf_cap={leaf_cap} prefixes={total_prefixes}")

        self._stats = ExplorationStatistics(
            start_time=time.time(),
            total_prefixes=total_prefixes,
        )

        per_prefix = self._initialize_prefix_states(valid_paths)
        results = self._explore_loop(per_prefix, leaf_cap)

        if self.config.afterwards_backtrack_target:
            results = self._compute_backtrack_targets(per_prefix, results)

        logger.debug(
            f"[EXPLORE] t={t} | "
            f"total_time={self._stats.elapsed_time():.2f}s | "
            f"total_nodes={self._stats.total_nodes_explored} | "
            f"solver_calls={self._stats.solver_calls}"
        )
        self._stats = None
        return results

    def _initialize_prefix_states(
        self, valid_paths: list[DiligentDatasetItem]
    ) -> list[PrefixState]:
        per_prefix: list[PrefixState] = []
        for idx, (prefix_ctx, _) in enumerate(valid_paths):
            nodes = prefix_ctx.nodes
            prefix_gold_len = prefix_ctx.gold_length

            per_prefix.append(
                PrefixState(
                    stack=[
                        Frontier(prefix_idx=idx, context=prefix_ctx, depth=0, children=0)
                    ],
                    prefix_gold_node_id=nodes[-1].identifier,
                    success_path_node_ids={node.identifier for node in prefix_ctx},
                    leaves_seen=0,
                    discovered_nodes=0,
                    solutions=[],
                    failed=[],
                    max_depth_abs=self.config.get_max_depth(
                        prefix_gold_len=prefix_gold_len
                    ),
                    is_completed=False,
                )
            )
        return per_prefix

    def _explore_loop(
        self, per_prefix: list[PrefixState], leaf_cap: int
    ) -> list[ExploreResult]:
        for _ in range(self._max_loops):
            frontiers_by_max_actions = self._collect_frontiers_by_max_actions(
                per_prefix=per_prefix,
                leaf_cap=leaf_cap,
            )

            if not frontiers_by_max_actions:
                break

            for max_actions, frontiers in frontiers_by_max_actions.items():
                batched_actions = self._generate_batch_actions(
                    items=frontiers,
                    max_actions=max_actions,
                )
                self._process_frontiers(frontiers, batched_actions, per_prefix)

        return [(st.solutions, st.failed) for st in per_prefix]

    def _collect_frontiers_by_max_actions(
        self, per_prefix: list[PrefixState], leaf_cap: int
    ) -> dict[int, list[Frontier]]:
        grouped: dict[int, list[Frontier]] = defaultdict(list)
        total_collected = 0

        for state in per_prefix:
            if total_collected >= self.config.explore_batch_size:
                break

            if not state.stack or state.leaves_seen >= leaf_cap:
                if not state.is_completed:
                    state.is_completed = True
                    if self._stats is not None:
                        self._stats.prefixes_completed += 1
                        self._log_progress()

                if state.leaves_seen >= leaf_cap:
                    state.stack.clear()
                continue

            sampled = self._sample_frontiers(state)

            for frontier in sampled:
                scheduled = int(
                    self._max_actions_fn(
                        self._current_t, frontier.depth, self.config.branching_factor
                    )
                )

                max_actions = min(scheduled, max(1, int(frontier.requested_children)))

                grouped[max_actions].append(frontier)
                total_collected += 1

        return grouped

    def _generate_batch_actions(
        self, items: list[Frontier], max_actions: int
    ) -> list[list[Action]]:
        try:
            ctxs = [item.context for item in items]
            proposed_actions, solver_calls = self.solver.propose_actions_processed(
                contexts=ctxs,
                t=self._current_t,
                max_actions=max_actions,
            )
            if self._stats is not None:
                self._stats.solver_calls += solver_calls
            return proposed_actions
        except Exception as e:
            logger.error(
                f"[EXPLORE] Batch generation failed (max_actions={max_actions}): {e}"
            )
            return [[] for _ in items]

    def _process_frontiers(
        self,
        frontiers: list[Frontier],
        batched_actions: list[list[Action]],
        per_prefix: list[PrefixState],
    ) -> None:
        for frontier, candidates in zip(frontiers, batched_actions):
            state = per_prefix[frontier.prefix_idx]
            max_children = int(self._max_children_for_frontier(frontier))
            remaining_capacity = max(0, max_children - frontier.children)
            want = min(int(frontier.requested_children), remaining_capacity)

            if want <= 0:
                if remaining_capacity > 0:
                    state.stack.append(frontier)
                continue

            candidates = candidates[:want]
            if not candidates:
                continue

            produced = len(candidates)
            frontier.children += produced
            state.discovered_nodes += produced

            if self._stats is not None:
                self._stats.total_nodes_explored += produced

            if frontier.children < max_children:
                state.stack.append(frontier)

            done_actions: list[DoneAction] = [
                a for a in candidates if isinstance(a, DoneAction)
            ]
            node_actions: list[NodeAction] = [
                a for a in candidates if isinstance(a, NodeAction)
            ]
            ordered = done_actions + node_actions

            if self.config.allow_backtracks:
                ordered += [a for a in candidates if isinstance(a, BacktrackAction)]

            for action in ordered:
                self._process_action(state, frontier, action)

    def _process_action(
        self, state: PrefixState, frontier: Frontier, action: Action
    ) -> None:
        ctx = frontier.context

        if self.config.always_renumber_node_id and isinstance(action, NodeAction):
            action.node_id = ctx.previous_node_action_id + 1

        if self.is_duplicate(state, ctx, action):
            return

        depth_abs = len(ctx)
        parent_state = ctx.last_state
        new_state = self.config.state_engine.reduce(parent_state, action)
        state.appearance_counter += 1
        new_ctx, *_ = ctx.renumber_with_append(
            action,
            new_state=new_state,
            appearance_order=state.appearance_counter,
        )

        validation_result = self.validator.validate(action, ctx)
        if validation_result is not None and not isinstance(action, BacktrackAction):
            self._add_failed_leaf(
                state=state,
                ctx=new_ctx,
                depth=max(len(new_ctx) - 1, 0),
                backtrack_reason=validation_result.comment,
            )
            return

        hard_depth_violation = depth_abs >= state.max_depth_abs
        done_depth_violation = (
            depth_abs == (state.max_depth_abs - 1)
        ) and not isinstance(action, DoneAction)
        if hard_depth_violation or done_depth_violation:
            self._add_failed_leaf(
                state,
                new_ctx,
                depth=depth_abs,
                backtrack_reason=f"Depth {depth_abs + 1} >= {state.max_depth_abs}",
            )
            return

        if isinstance(action, DoneAction):
            self._add_success_leaf(state, ctx, action)
            return

        if isinstance(action, NodeAction):
            state.stack.append(
                Frontier(
                    prefix_idx=frontier.prefix_idx,
                    context=new_ctx,
                    depth=frontier.depth + 1,
                    children=0,
                    requested_children=1,
                )
            )
            return

        if isinstance(action, BacktrackAction):
            self._add_backtrack_leaf(
                state=state,
                ctx=new_ctx,
                action=action,
                depth=depth_abs + 1,
            )
            return

    def _add_success_leaf(
        self, state: PrefixState, ctx: PathContext, done_action: DoneAction
    ) -> None:
        new_ctx, _ = ctx.renumbered()
        state.solutions.append((new_ctx, done_action))
        state.leaves_seen += 1
        state.success_path_node_ids.update(
            [node.identifier for node in ctx.nodes[-1].path()]
        )

    def _add_failed_leaf(
        self,
        state: PrefixState,
        ctx: PathContext,
        depth: Optional[int] = None,
        backtrack_reason: str = "failed",
    ) -> None:
        state.leaves_seen += 1

        target_action_id = -1
        if not self.config.afterwards_backtrack_target:
            target_action_id = self._lca_node(
                ctx.nodes, success_path_node_ids=state.success_path_node_ids
            )

        backtrack_action = BacktrackAction(target_action_id, reason=backtrack_reason)
        state.failed.append((ctx, backtrack_action))

        if self.training_logger is not None:
            log_depth = depth if depth is not None else max(len(ctx) - 1, 0)
            self.training_logger.log_backtrack_event(
                phase="SFT-B",
                t=self._current_t,
                depth=log_depth,
                path_nodes=ctx.nodes,
                backtrack_action=backtrack_action,
            )

    def _add_backtrack_leaf(
        self,
        state: PrefixState,
        ctx: PathContext,
        action: BacktrackAction,
        depth: Optional[int] = None,
    ) -> None:
        state.leaves_seen += 1
        state.failed.append((ctx, action))

        if self.training_logger is not None:
            log_depth = depth if depth is not None else max(len(ctx) - 1, 0)
            self.training_logger.log_backtrack_event(
                phase="SFT-B",
                t=self._current_t,
                depth=log_depth,
                path_nodes=ctx.nodes,
                backtrack_action=action,
            )

    @staticmethod
    def add_to_dataset(
        dataset: DiligentDatasetView, results: list[ExploreResult]
    ) -> list[tuple[PathContext, Action]]:
        """Batch-add exploration results to reduce overhead."""
        to_add: list[tuple[PathContext, Action]] = []
        for solutions, failed_leaves in results:
            for ren_ctx, done in solutions:
                to_add.append((ren_ctx, done))
            for ren_ctx, backtrack in failed_leaves:
                to_add.append((ren_ctx, backtrack))

        dataset.add_exploration_pairs(to_add)
        return to_add
