"""Core data structures for reasoning paths and nodes."""

from itertools import count
from typing import Any, Iterator, Optional

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction


class Node[T]:
    """
    Represents a node in the reasoning tree.

    Attributes:
        id: Unique object identifier (for graph structure)
        parent: Parent node in the tree
        action: Action that produced this node
        state: Computed state (from StateEngine.reduce)
        appearance_order: Order of appearance in exploration context
            - 0 for nodes already in context
            - >0 for newly explored nodes
    """

    __slots__ = ("id", "parent", "action", "state", "appearance_order")

    _id_counter = count(0)

    def __init__(
        self,
        parent: Optional["Node"],
        action: Action,
        identifier: Optional[int] = None,
        state: Optional[T] = None,
        appearance_order: int = 0,
    ):
        self.id = identifier if identifier is not None else next(Node._id_counter)
        self.parent = parent
        self.action = action
        self.state = state
        self.appearance_order = appearance_order

    @property
    def identifier(self) -> int:
        return self.id

    def set_identifier(self, identifier: int):
        """WARNING: Usually SHOULD NOT be used. Just for utility needs."""
        self.id = identifier

    def path(self) -> list["Node"]:
        """Return path from root to this node."""
        if self.parent is None:
            return [self]
        return self.parent.path() + [self]

    def __str__(self):
        return f"[{self.action}]"


class PathContext[T]:
    """
    Wrapper around a sequence of nodes with metadata.

    Provides pyligent.common.utils for renumbering, state access, and path analysis.
    """

    @staticmethod
    def _build_complete_path_from_root(
        nodes: list[Node[T]], root: Node[T]
    ) -> list[Node[T]]:
        """
        Build complete path from root by following parent-child relationships.
        Uses nodes in the current PathContext to guide reconstruction.
        """
        path = [root]
        seen = {id(root)}

        # Create mapping of parent_id -> children for known nodes
        parent_to_children: dict[int, list[Node]] = {}
        for node in nodes:
            if node.parent is not None:
                parent_id = id(node.parent)
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                parent_to_children[parent_id].append(node)

        # Follow chain from root
        current = root
        safety_counter = 0
        max_hops = 256

        while safety_counter < max_hops:
            safety_counter += 1

            if isinstance(current.action, DoneAction):
                break

            current_id = id(current)
            children = parent_to_children.get(current_id, [])

            if not children:
                break

            # Take first unvisited child
            next_node = None
            for child in children:
                if id(child) not in seen:
                    next_node = child
                    break

            if next_node is None:
                break

            path.append(next_node)
            seen.add(id(next_node))
            current = next_node

        return path

    def __init__(
        self,
        nodes: list[Node[T]],
        gold_length: Optional[int] = None,
    ):
        self.nodes = nodes
        self._explicit_gold_length = gold_length

        # Track last NodeAction for ID sequencing
        node_action_id = -1
        prev_node_action: Optional[Node] = None

        for node in self.nodes:
            if isinstance(node.action, NodeAction):
                node_action_id = node.action.node_id
                prev_node_action = node

        self._previous_node_action_id = node_action_id
        self._previous_node_action = prev_node_action

        self._cached_fingerprint: Optional[int] = None

    def __getitem__(self, idx: int) -> Node:
        return self.nodes[idx]

    @property
    def fingerprint(self) -> int:
        """Fast integer fingerprint for deduplication (cached)."""
        if self._cached_fingerprint is None:
            # Use tuple of action hashes for O(n) computation, cached thereafter
            self._cached_fingerprint = hash(
                tuple(n.action.hash_value for n in self.nodes)
            )
        return self._cached_fingerprint

    def _compute_path_hash(self) -> int:
        """Compute hash of node sequence for cache invalidation."""
        return hash(tuple(self.nodes))

    def get_node_by_id(self, node_id: int) -> Optional[Node]:
        """Find node by NodeAction.node_id."""
        for node in self.nodes:
            if isinstance(node.action, NodeAction) and node.action.node_id == node_id:
                return node
        return None

    @property
    def gold_length(self) -> Optional[int]:
        """Get cached gold length, recomputing if path changed."""
        if self._explicit_gold_length is not None:
            return self._explicit_gold_length
        return None

    @property
    def previous_node_action_id(self) -> int:
        """Get last NodeAction.node_id in this context."""
        return self._previous_node_action_id

    @property
    def previous_node_action(self) -> Optional[Node]:
        """Get last node containing NodeAction."""
        return self._previous_node_action

    @property
    def last_state(self) -> Optional[Any]:
        """Get state of the last node in context."""
        return self.nodes[-1].state if self.nodes else None

    def __str__(self) -> str:
        return " | ".join(str(n.action) for n in self.nodes)

    @property
    def dense_str(self) -> str:
        """Compact string representation for hashing."""
        return "|".join(n.action.dense_str for n in self.nodes)

    @property
    def hash_value(self) -> int:
        """Hash based on dense_str for deduplication."""
        return hash(self.dense_str)

    @property
    def last_node(self) -> Node:
        return self.nodes[-1]

    def __len__(self):
        return len(self.nodes)

    def renumbered(self) -> tuple["PathContext", dict[int, int]]:
        """
        Return (new_context, old_to_new_id_map) with sequential NodeAction IDs.

        NodeAction.node_id and BacktrackAction.target_id are remapped to
        sequential integers starting from 0.
        """
        mapping: dict[int, int] = {}
        new_nodes: list[Node] = []
        node_action_id = 0

        for old_node in self.nodes:
            if isinstance(old_node.action, NodeAction):
                old_id = old_node.action.node_id
                new_action = NodeAction(node_action_id, old_node.action.text)
                mapping[old_id] = node_action_id
                node_action_id += 1
            elif isinstance(old_node.action, BacktrackAction):
                # Placeholder, patch later
                new_action = BacktrackAction(
                    old_node.action.target_id, old_node.action.reason
                )
            elif isinstance(old_node.action, DoneAction):
                new_action = DoneAction(old_node.action.answer)
            else:
                raise ValueError(f"Unknown action type: {type(old_node.action)}")

            new_parent = new_nodes[-1] if new_nodes else None
            new_node = Node(
                new_parent,
                new_action,
                identifier=old_node.identifier,
                state=old_node.state,
                appearance_order=old_node.appearance_order,
            )
            new_nodes.append(new_node)

        # Patch BacktrackAction targets
        for new_node in new_nodes:
            if isinstance(new_node.action, BacktrackAction):
                old_target = new_node.action.target_id
                new_target = mapping.get(old_target, 0)
                new_node.action = BacktrackAction(new_target, new_node.action.reason)

        return PathContext(new_nodes, gold_length=self.gold_length), mapping

    def renumber_with_append(
        self,
        new_action: Action,
        new_state: Any,
        appearance_order: int,
        last_mapping: Optional[dict[int, int]] = None,
        next_id: Optional[int] = None,
    ) -> tuple["PathContext", dict[int, int], int]:
        """
        Incrementally renumber by appending one action.

        Args:
            new_action: Action to append
            new_state: State for new node
            appearance_order: Appearance order for new node
            last_mapping: Previous old->new ID mapping (for reuse)
            next_id: Next available NodeAction ID

        Returns:
            (new_context, updated_mapping, next_available_id)
        """
        # Initialize mapping if not provided
        if last_mapping is None or next_id is None:
            ren_ctx, mapping = self.renumbered()
            next_id = 1 + max(mapping.values(), default=-1)
        else:
            ren_ctx = self
            mapping = dict(last_mapping)

        parent = ren_ctx.nodes[-1] if ren_ctx.nodes else None

        # Renumber the new action
        if isinstance(new_action, NodeAction):
            assigned_id = next_id
            old_id = new_action.node_id  # capture solver-proposed id
            new_action = NodeAction(assigned_id, new_action.text)
            mapping[old_id] = assigned_id  # FIX: map old -> new
            next_id += 1
        elif isinstance(new_action, BacktrackAction):
            new_target = mapping.get(new_action.target_id, 0)
            new_action = BacktrackAction(new_target, new_action.reason)
        elif isinstance(new_action, DoneAction):
            pass  # No ID to renumber

        # Create new node with state and appearance order
        appended = Node(
            parent,
            new_action,
            identifier=None,
            state=new_state,
            appearance_order=appearance_order,
        )

        new_ctx = PathContext(ren_ctx.nodes + [appended], gold_length=self.gold_length)

        new_ctx._cached_fingerprint = None

        return new_ctx, mapping, next_id


class GoldPath[T]:
    """Represents the golden chain of reasoning (nodes + final done)."""

    def __init__(self, nodes: list[Node[T]]):
        assert len(nodes) >= 2, "Gold path should have length at least 2"
        assert isinstance(nodes[-1].action, DoneAction), (
            "Gold path should end with DoneAction"
        )
        self.nodes = nodes

    def __str__(self):
        return " -> ".join(str(n.action) for n in self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, idx: int) -> Node:
        return self.nodes[idx]

    def __iter__(self) -> Iterator[Node]:
        return iter(self.nodes)
