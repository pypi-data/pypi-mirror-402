from typing import Callable, Optional

from pyligent.core.action import NodeAction
from pyligent.core.path import Node

BacktrackPolicyFn = Callable[[list[Node], Optional[list[Node]], Node], int]
# (failed_path, success_path_nodes, prev_gold_node) -> target id


def default_backtrack_policy(
    failed_path: list[Node],
    success_path_nodes: Optional[list[Node]],
    prev_gold_node: Node,
) -> int:
    """
    Default backtrack policy: LCA with success path if available, else prev_gold_node.

    Returns:
        Target NodeAction.node_id for backtracking
    """
    if success_path_nodes is not None:
        # Find LCA
        lca = failed_path[0]
        success_set = set(success_path_nodes)
        for node in failed_path:
            if node in success_set:
                lca = node
            else:
                break
        if isinstance(lca.action, NodeAction):
            return lca.action.node_id

    # Fallback to prev_gold_node
    if isinstance(prev_gold_node.action, NodeAction):
        return prev_gold_node.action.node_id

    # TODO: Check. Should be unreachable, but it is reachable
    # Ultimate fallback: root (id=0)
    return 0
