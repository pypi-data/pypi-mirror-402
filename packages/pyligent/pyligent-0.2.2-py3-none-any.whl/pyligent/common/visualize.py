import json
from collections import deque
from pathlib import Path
from typing import Any, Optional

import networkx as nx
import yaml
from loguru import logger

from pyligent.core.action import BacktrackAction, DoneAction, NodeAction
from pyligent.core.explorer import FailedLeaf, PathContext, SuccessLeaf
from pyligent.core.path import Node


class DFSVisualizer:
    """
    Enhanced DFS exploration tree visualizer using NetworkX and Cytoscape.js.
    Provides interactive, draggable tree visualization with clear edge routing.
    """

    METADATA_FILE = "dfs_visualizer_metadata.json"

    def __init__(
        self, output_dir: Path, folder_prefix: str = "dfs", max_text_length: int = 50
    ):
        """Initialize the visualizer with output directory."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.folder_prefix = folder_prefix
        self.metadata_path = self.output_dir / self.METADATA_FILE

        self._max_text_length = max_text_length

    def _load_metadata(self) -> dict[int, dict[str, Any]]:
        """Load metadata from disk."""
        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                return {int(k): v for k, v in raw.items()}
        return {}

    def _save_metadata(self, metadata: dict[int, dict[str, Any]]) -> None:
        """Save metadata to disk."""
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {str(k): v for k, v in metadata.items()},
                f,
                indent=2,
                ensure_ascii=False,
            )
        # logger.debug(f"[Visualizer] Metadata saved to: {self.metadata_path.as_posix()}")

    def _update_metadata(self, step_t: int, step_info: dict[str, Any]) -> None:
        """Update metadata for a specific step and regenerate global index."""
        metadata = self._load_metadata()
        metadata[step_t] = step_info
        self._save_metadata(metadata)
        self._regenerate_global_index(metadata)

    def visualize(
        self,
        path_contexts: list[PathContext],
        solutions_list: list[list[SuccessLeaf]],
        failed_leaves_list: list[list[FailedLeaf]],
        path: Optional[Path] = None,
        base_name: str = "tree",
        step_t: Optional[int] = None,
    ) -> str:
        """Visualize multiple exploration trees."""
        if not (len(path_contexts) == len(solutions_list) == len(failed_leaves_list)):
            raise ValueError(
                "path_contexts, solutions_list, and failed_leaves_list must have the same length"
            )

        if path is None and step_t is not None:
            path = Path(f"{self.folder_prefix}_{step_t}")

        output_path = self.output_dir / path if path is not None else self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        index_html = self._visualize_all_html(
            path_contexts,
            solutions_list,
            failed_leaves_list,
            base_name,
            output_path,
            step_t=step_t,
        )

        # Update metadata if step_t provided
        if step_t is not None:
            step_info = {
                "step_t": step_t,
                "path": path.as_posix() if path else "",
                "index_file": f"{path.as_posix()}/{base_name}_index.html"
                if path
                else f"{base_name}_index.html",
                "tree_count": len(path_contexts),
                "total_nodes": sum(len(ctx.nodes) for ctx in path_contexts),
                "total_success": sum(len(sols) for sols in solutions_list),
                "total_failed": sum(len(fails) for fails in failed_leaves_list),
            }
            self._update_metadata(step_t, step_info)

        return index_html

    def _serialize_node(self, node: Node) -> dict[str, Any]:
        """Serialize a Node object to a dictionary."""
        return {
            "identifier": node.identifier,
            "parent_id": node.parent.identifier if node.parent else None,
            "appearance_order": node.appearance_order,
            "action": {
                "type": type(node.action).__name__,
                "text": node.action.text,
                # For NodeAction
                "node_id": getattr(node.action, "node_id", None),
                # For BacktrackAction
                "target_id": getattr(node.action, "target_id", None),
                "reason": getattr(node.action, "reason", None),
            },
        }

    def _serialize_path_context_nodes(self, path_ctx_nodes: list[Node]) -> dict[str, Any]:
        """Serialize PathContext to a dictionary."""
        return {"nodes": [self._serialize_node(node) for node in path_ctx_nodes]}

    def _serialize_success_path(self, success_leaf: SuccessLeaf) -> dict[str, Any]:
        """Serialize SuccessPath (tuple of PathContext and terminal Node) to dict."""
        success_path, done = success_leaf
        return {
            "context": self._serialize_path_context_nodes(success_path.nodes),
            "terminal_node": {"answer": done.answer},
        }

    def _serialize_failed_leaf(self, failed_leaf: FailedLeaf) -> dict[str, Any]:
        """Serialize FailedLeaf (tuple of PathContext, Node, BacktrackAction) to dict."""
        fail_ctx, backtrack = failed_leaf
        path_nodes = fail_ctx.nodes
        return {
            "context": self._serialize_path_context_nodes(path_nodes[:-1]),
            "fail_node": self._serialize_node(path_nodes[-1]),
            "backtrack": {
                "type": type(backtrack).__name__,
                "text": backtrack.text,
                "target_id": backtrack.target_id,
                "reason": getattr(backtrack, "reason", None),
            },
        }

    def _save_tree_data_to_yaml(
        self,
        tree_index: int,
        path_ctx: PathContext,
        solutions: list[SuccessLeaf],
        failed_leaves: list[FailedLeaf],
        output_path: Path,
        base_name: str,
    ) -> None:
        """Save tree data to YAML file for later reconstruction."""
        tree_data = {
            "tree_index": tree_index,
            "prefix_path": self._serialize_path_context_nodes(path_ctx.nodes),
            "success_paths": [self._serialize_success_path(sp) for sp in solutions],
            "failed_leaves": [self._serialize_failed_leaf(fl) for fl in failed_leaves],
        }

        # Save to YAML file next to HTML
        trees_dir = output_path / "trees"
        trees_dir.mkdir(parents=True, exist_ok=True)
        yaml_file = trees_dir / f"{base_name}_{tree_index}.yaml"

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(
                tree_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def _deserialize_node(
        self, node_data: dict[str, Any], nodes_cache: dict[int, Node]
    ) -> Node:
        """Deserialize a Node from dictionary."""
        node_id = node_data["identifier"]

        # Check if already created (for parent references)
        if node_id in nodes_cache:
            return nodes_cache[node_id]

        # Get parent
        parent = None
        if node_data["parent_id"] is not None:
            parent = nodes_cache.get(node_data["parent_id"])

        # Reconstruct action
        action_data = node_data["action"]
        action_type = action_data["type"]

        if action_type == "NodeAction":
            action = NodeAction(node_id=action_data["node_id"], text=action_data["text"])
        elif action_type == "DoneAction":
            action = DoneAction(answer=action_data["text"])
        elif action_type == "BacktrackAction":
            action = BacktrackAction(
                target_id=action_data["target_id"],
                reason=action_data.get("reason"),
            )
        else:
            raise ValueError(f"Unknown action type: {action_type}")

        # Create node
        node = Node(
            parent=parent,
            action=action,
            appearance_order=node_data.get("appearance_order", 0),
        )
        node.set_identifier(node_id)
        nodes_cache[node_id] = node

        return node

    def _deserialize_path_context_nodes(
        self, ctx_data: dict[str, Any], nodes_cache: dict[int, Node]
    ) -> list[Node]:
        """Deserialize PathContext from dictionary."""
        return [
            self._deserialize_node(node_data, nodes_cache)
            for node_data in ctx_data["nodes"]
        ]

    def _deserialize_success_path(
        self, sp_data: dict[str, Any], nodes_cache: dict[int, Node]
    ) -> SuccessLeaf:
        """Deserialize SuccessPath from dictionary."""
        sol_nodes = self._deserialize_path_context_nodes(sp_data["context"], nodes_cache)
        done = DoneAction(
            answer=sp_data["terminal_node"].get("answer", ""),
        )

        return (PathContext(sol_nodes), done)

    def _deserialize_failed_leaf(
        self, fl_data: dict[str, Any], nodes_cache: dict[int, Node]
    ) -> FailedLeaf:
        """Deserialize FailedLeaf from dictionary."""
        fail_ctx_nodes = self._deserialize_path_context_nodes(
            fl_data["context"], nodes_cache
        )
        fail_node = self._deserialize_node(fl_data["fail_node"], nodes_cache)

        # Reconstruct backtrack action
        backtrack_data = fl_data["backtrack"]
        backtrack = BacktrackAction(
            target_id=backtrack_data["target_id"],
            reason=backtrack_data.get("reason"),
        )

        return (PathContext(fail_ctx_nodes + [fail_node]), backtrack)

    def _load_tree_data_from_yaml(self, yaml_file: Path) -> dict[str, Any]:
        """Load tree data from YAML file."""
        with open(yaml_file, "r", encoding="utf-8") as f:
            tree_data = yaml.safe_load(f)

        # Deserialize with nodes cache to maintain references
        nodes_cache: dict[int, Node] = {}

        prefix_path_nodes = self._deserialize_path_context_nodes(
            tree_data["prefix_path"], nodes_cache
        )
        prefix_path = PathContext(prefix_path_nodes)
        success_paths = [
            self._deserialize_success_path(sp, nodes_cache)
            for sp in tree_data["success_paths"]
        ]
        failed_leaves = [
            self._deserialize_failed_leaf(fl, nodes_cache)
            for fl in tree_data["failed_leaves"]
        ]

        return {
            "tree_index": tree_data["tree_index"],
            "prefix_path": prefix_path,
            "success_paths": success_paths,
            "failed_leaves": failed_leaves,
        }

    def _regenerate_global_index(self, metadata: dict[int, dict[str, Any]]) -> None:
        """Generate global index page from metadata."""
        if not metadata:
            logger.warning("[Visualizer] No metadata available to generate global index")
            return

        step_items = []
        total_trees = 0
        total_nodes = 0
        total_success = 0
        total_failed = 0

        for step_t in sorted(metadata.keys()):
            info = metadata[step_t]
            step_items.append(
                f'''
            <tr>
                <td data-value="{info["step_t"]}">{info["step_t"]}</td>
                <td data-value="{info["tree_count"]}">{info["tree_count"]}</td>
                <td data-value="{info["total_nodes"]}">{info["total_nodes"]}</td>
                <td data-value="{info["total_success"]}" class="success-cell">{info["total_success"]}</td>
                <td data-value="{info["total_failed"]}" class="failed-cell">{info["total_failed"]}</td>
                <td><a href="{info["index_file"]}" class="view-btn">View Step {info["step_t"]}</a></td>
            </tr>
        '''
            )
            total_trees += info["tree_count"]
            total_nodes += info["total_nodes"]
            total_success += info["total_success"]
            total_failed += info["total_failed"]

        steps_table = "\n".join(step_items)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon"
        href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏞️</text></svg>">
    <title>{self.folder_prefix.upper()} - Global Index</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        header p {{
            font-size: 16px;
            opacity: 0.95;
        }}

        .content {{
            padding: 40px;
        }}

        h2 {{
            font-size: 24px;
            margin-bottom: 25px;
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        th {{
            background: #f8f9fa;
            color: #495057;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 14px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            cursor: pointer;
            user-select: none;
        }}

        th:hover {{
            background: #e9ecef;
        }}

        th.sortable:after {{
            content: ' ⇅';
            opacity: 0.5;
        }}

        th.sorted-asc:after {{
            content: ' ▲';
            opacity: 1;
        }}

        th.sorted-desc:after {{
            content: ' ▼';
            opacity: 1;
        }}

        td {{
            padding: 14px;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
            font-size: 14px;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .success-cell {{
            color: #2E7D32;
            font-weight: 600;
        }}

        .failed-cell {{
            color: #C62828;
            font-weight: 600;
        }}

        .view-btn {{
            display: inline-block;
            padding: 8px 16px;
            background: #4A90E2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            font-size: 13px;
            transition: all 0.2s;
        }}

        .view-btn:hover {{
            background: #357ABD;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .summary-card h3 {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .summary-card p {{
            font-size: 32px;
            font-weight: 700;
            color: #333;
        }}

        .summary-card.success {{
            background: linear-gradient(135deg, #81C784 0%, #66BB6A 100%);
        }}

        .summary-card.success h3,
        .summary-card.success p {{
            color: white;
        }}

        .summary-card.failed {{
            background: linear-gradient(135deg, #E57373 0%, #EF5350 100%);
        }}

        .summary-card.failed h3,
        .summary-card.failed p {{
            color: white;
        }}

        .summary-card.trees {{
            background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
        }}

        .summary-card.trees h3,
        .summary-card.trees p {{
            color: white;
        }}

        .summary-card.nodes {{
            background: linear-gradient(135deg, #FFB74D 0%, #FFA726 100%);
        }}

        .summary-card.nodes h3,
        .summary-card.nodes p {{
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌳 {self.folder_prefix.upper()} - Global Index</h1>
            <p>Aggregated exploration results across all training steps</p>
        </header>

        <div class="content">
            <h2>📊 Overview</h2>
            <div class="summary">
                <div class="summary-card">
                    <h3>Total Steps</h3>
                    <p>{len(metadata)}</p>
                </div>
                <div class="summary-card trees">
                    <h3>Total Trees</h3>
                    <p>{total_trees}</p>
                </div>
                <div class="summary-card nodes">
                    <h3>Total Nodes</h3>
                    <p>{total_nodes}</p>
                </div>
                <div class="summary-card success">
                    <h3>Success Paths</h3>
                    <p>{total_success}</p>
                </div>
                <div class="summary-card failed">
                    <h3>Failed Paths</h3>
                    <p>{total_failed}</p>
                </div>
            </div>

            <h2>📋 Training Steps (Click headers to sort)</h2>
            <table id="steps-table">
                <thead>
                    <tr>
                        <th class="sortable" data-column="0">Step (t)</th>
                        <th class="sortable" data-column="1">Trees</th>
                        <th class="sortable" data-column="2">Nodes</th>
                        <th class="sortable" data-column="3">Success</th>
                        <th class="sortable" data-column="4">Failed</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                    {steps_table}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const table = document.getElementById('steps-table');
        const headers = table.querySelectorAll('th.sortable');
        const tbody = document.getElementById('table-body');

        let currentSort = {{ column: -1, ascending: true }};

        headers.forEach(header => {{
            header.addEventListener('click', function() {{
                const column = parseInt(this.dataset.column);
                const ascending = currentSort.column === column ? !currentSort.ascending : true;

                sortTable(column, ascending);

                headers.forEach(h => {{
                    h.classList.remove('sorted-asc', 'sorted-desc');
                }});
                this.classList.add(ascending ? 'sorted-asc' : 'sorted-desc');

                currentSort = {{ column, ascending }};
            }});
        }});

        function sortTable(column, ascending) {{
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {{
                const aValue = parseFloat(a.cells[column].dataset.value);
                const bValue = parseFloat(b.cells[column].dataset.value);

                return ascending ? aValue - bValue : bValue - aValue;
            }});

            rows.forEach(row => tbody.removeChild(row));
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>"""

        global_index_file = self.output_dir / f"{self.folder_prefix}.html"
        global_index_file.write_text(html, encoding="utf-8")
        # logger.debug(f"[Visualizer] Global index updated: {global_index_file.as_posix()}")

    def rebuild_html_from_yaml(
        self,
        index_folder: Path,
        base_name: str = "tree",
        step_t: Optional[int] = None,
    ) -> str:
        """Rebuild HTML visualizations from YAML files."""
        trees_dir = index_folder / "trees"

        if not trees_dir.exists():
            raise ValueError(f"Trees directory not found: {trees_dir}")

        yaml_files = sorted(trees_dir.glob(f"{base_name}_*.yaml"))

        if not yaml_files:
            raise ValueError(f"No YAML files found in {trees_dir}")

        logger.info(f"[Visualizer] Found {len(yaml_files)} YAML files to rebuild")

        path_contexts = []
        solutions_list = []
        failed_leaves_list = []

        for yaml_file in yaml_files:
            logger.info(f"[Visualizer] Loading {yaml_file.name}...")
            tree_data = self._load_tree_data_from_yaml(yaml_file)
            path_contexts.append(tree_data["prefix_path"])
            solutions_list.append(tree_data["success_paths"])
            failed_leaves_list.append(tree_data["failed_leaves"])

        logger.info("[Visualizer] Rebuilding HTML visualizations...")
        index_html = self._visualize_all_html(
            path_contexts,
            solutions_list,
            failed_leaves_list,
            base_name,
            index_folder,
            step_t=step_t,
        )

        # Update metadata if step_t provided
        if step_t is not None:
            relative_path = index_folder.relative_to(self.output_dir)
            step_info = {
                "step_t": step_t,
                "path": relative_path.as_posix(),
                "index_file": f"{relative_path.as_posix()}/{base_name}_index.html",
                "tree_count": len(path_contexts),
                "total_nodes": sum(len(ctx.nodes) for ctx in path_contexts),
                "total_success": sum(len(sols) for sols in solutions_list),
                "total_failed": sum(len(fails) for fails in failed_leaves_list),
            }
            self._update_metadata(step_t, step_info)

        return index_html

    def _visualize_all_html(
        self,
        path_contexts: list[PathContext],
        solutions_list: list[list[SuccessLeaf]],
        failed_leaves_list: list[list[FailedLeaf]],
        base_name: str,
        output_path: Path,
        step_t: Optional[int] = None,
    ) -> str:
        """Generate HTML visualizations for all trees plus an index page."""
        tree_stats = []

        # Generate individual tree visualizations
        for idx, (path_ctx, solutions, failed_leaves) in enumerate(
            zip(path_contexts, solutions_list, failed_leaves_list)
        ):
            # Save tree data to YAML FIRST (before building graph)
            self._save_tree_data_to_yaml(
                idx, path_ctx, solutions, failed_leaves, output_path, base_name
            )

            # Build graph for this tree
            self.graph = nx.DiGraph()
            self.node_attrs = {}
            self._add_prefix_path(path_ctx)
            prefix_length = len(path_ctx)
            self._add_solutions(solutions, prefix_length)
            self._add_failed_leaves(failed_leaves, prefix_length)

            # Calculate statistics
            stats: dict[str, Any] = self._calculate_statistics()
            stats["total_nodes"] = len(self.graph.nodes)
            stats["total_edges"] = len(self.graph.edges)
            stats["tree_index"] = idx
            stats["filename"] = f"trees/{base_name}_{idx}.html"

            # Calculate leaves
            leaves = stats["success"] + stats["failed"]
            stats["leaves"] = leaves
            tree_stats.append(stats)

            # Generate and save HTML visualization
            result = self._visualize_html_cytoscape(idx)

            # Create trees subdirectory
            trees_dir = output_path / "trees"
            trees_dir.mkdir(parents=True, exist_ok=True)
            output_file = trees_dir / f"{base_name}_{idx}.html"
            output_file.write_text(result, encoding="utf-8")

        # Generate index page
        index_html = self._generate_index_page(tree_stats, step_t=step_t)
        index_file = output_path / f"{base_name}_index.html"
        index_file.write_text(index_html, encoding="utf-8")

        logger.debug(f"[Visualizer] DFS HTML saved to: {index_file.as_posix()}")
        return index_html

    def _calculate_node_levels(self) -> dict:
        """Calculate the level/depth of each node for hierarchical layout."""
        levels = {}
        # Find root nodes
        roots = [n for n in self.graph.nodes if self.graph.in_degree(n) == 0]
        if not roots:
            min_degree = min(self.graph.in_degree(n) for n in self.graph.nodes)
            roots = [n for n in self.graph.nodes if self.graph.in_degree(n) == min_degree]

        # BFS to assign levels
        queue = deque()
        for root in roots:
            queue.append((root, 0))
            levels[root] = 0

        while queue:
            node, level = queue.popleft()
            for child in self.graph.successors(node):
                edge_data = self.graph.edges[node, child]
                edge_type = edge_data.get("edge_type", "normal")

                if edge_type == "backtrack":
                    if child not in levels:
                        levels[child] = level
                else:
                    if child not in levels:
                        levels[child] = level + 1
                        queue.append((child, level + 1))
                    elif levels[child] > level + 1:
                        levels[child] = level + 1
                        queue.append((child, level + 1))

        return levels

    def _node_id(self, node: Node) -> str:
        return str(node.identifier)

    def _node_status(self, node: Node, prefix: bool) -> str:
        if prefix:
            return "prefix"
        node_action = node.action
        if isinstance(node_action, NodeAction):
            return "explored"
        if isinstance(node_action, BacktrackAction):
            return "failed"
        if isinstance(node_action, DoneAction):
            return "done"
        raise RuntimeError("Unknown action")

    def _add_node(
        self,
        node: Node,
        depth: int,
        ctx: PathContext,
        prefix: bool = False,
        is_leaf: bool = False,
    ) -> str:
        node_action = node.action
        node_id = self._node_id(node)
        node_status = self._node_status(node, prefix)

        self.graph.add_node(node_id)
        self.node_attrs[node_id] = {
            "action": node.action,
            "status": node_status,
            "text": node.action.text,
            "state": str(node.state),
            "depth": depth,
            "appearance_order": node.appearance_order,
            "is_leaf": is_leaf,
        }

        # Connect to parent if exists
        if node.parent:
            parent_id = self._node_id(node.parent)
            if parent_id in self.graph:
                self.graph.add_edge(parent_id, node_id, edge_type="normal")

        if isinstance(node_action, BacktrackAction):
            if node_action.reason:
                self.node_attrs[node_id]["backtrack_reason"] = node_action.reason
                self.node_attrs[node_id]["text"] = node_action.reason

            target_node = ctx.get_node_by_id(node_action.target_id)
            if target_node is None:
                return node_id
            target_identifier = str(target_node.identifier)
            self.node_attrs[node_id]["backtrack_target"] = target_identifier

            if target_identifier in self.graph:
                self.graph.add_edge(node_id, target_identifier, edge_type="backtrack")

        return node_id

    def _add_prefix_path(self, path_context: PathContext) -> None:
        """Add prefix path nodes to the graph from PathContext.nodes."""
        for idx, node in enumerate(path_context.nodes):
            self._add_node(node, idx, path_context, prefix=True)

    def _add_solutions(self, solutions: list[SuccessLeaf], prefix_length: int) -> None:
        """Add successful solution paths to the graph."""
        for sol_ctx, done in solutions:
            for idx, node in enumerate(sol_ctx.nodes[prefix_length:]):
                self._add_node(
                    node,
                    idx + prefix_length,
                    sol_ctx,
                )

            self._add_node(
                Node(
                    parent=sol_ctx.last_node,
                    action=done,
                    appearance_order=sol_ctx.last_node.appearance_order,
                ),
                len(sol_ctx),
                sol_ctx,
                is_leaf=True,
            )

    def _add_failed_leaves(
        self, failed_leaves: list[FailedLeaf], prefix_length: int
    ) -> None:
        """Add failed leaf nodes and backtrack edges to the graph."""
        for fail_ctx, backtrack in failed_leaves:
            for idx, node in enumerate(fail_ctx.nodes[prefix_length:]):
                self._add_node(node, idx + prefix_length, fail_ctx)
            self._add_node(
                Node(
                    parent=fail_ctx.last_node,
                    action=backtrack,
                    appearance_order=fail_ctx.last_node.appearance_order,
                ),
                len(fail_ctx),
                fail_ctx,
                is_leaf=True,
            )

    def _calculate_statistics(self) -> dict[str, Any]:
        """Calculate statistics for the current tree."""
        prefix_count = sum(
            1 for n in self.node_attrs.values() if n.get("status") == "prefix"
        )
        explored_count = sum(
            1 for n in self.node_attrs.values() if n.get("status") == "explored"
        )
        done_count = sum(
            1
            for n in self.node_attrs.values()
            if (n.get("is_leaf", False) and n.get("status") == "done")
        )
        failed_count = sum(
            1 for n in self.node_attrs.values() if n.get("status") == "failed"
        )

        return {
            "prefix": prefix_count,
            "explored": explored_count + done_count,
            "success": done_count,
            "failed": failed_count,
        }

    def _convert_to_cytoscape_json(self) -> dict:
        """Convert NetworkX graph to Cytoscape.js JSON format."""
        levels = self._calculate_node_levels()

        elements = []

        # Add nodes
        for node_id in self.graph.nodes:
            attrs = self.node_attrs[node_id]
            status = attrs["status"]

            # Determine node styling based on status
            node_classes = [status]
            if attrs.get("is_leaf", False):
                node_classes.append("leaf")

            elements.append(
                {
                    "data": {
                        "id": node_id,
                        "label": attrs["text"][: self._max_text_length]
                        + ("..." if len(attrs["text"]) > self._max_text_length else ""),
                        "full_text": attrs["text"].replace("\n", "<br>"),
                        "state": attrs["state"].replace("\n", "<br>"),
                        "status": status,
                        "depth": attrs["depth"],
                        "level": levels.get(node_id, 0),
                        "appearance_order": attrs["appearance_order"],
                        "is_leaf": attrs.get("is_leaf", False),
                        "backtrack_reason": attrs.get("backtrack_reason", ""),
                    },
                    "classes": " ".join(node_classes),
                }
            )

        # Add edges
        for source, target in self.graph.edges:
            edge_data = self.graph.edges[source, target]
            edge_type = edge_data.get("edge_type", "normal")

            elements.append(
                {
                    "data": {
                        "id": f"{source}-{target}",
                        "source": source,
                        "target": target,
                        "edge_type": edge_type,
                    },
                    "classes": edge_type,
                }
            )

        return {"elements": elements}

    def _visualize_html_cytoscape(self, tree_index: int) -> str:
        """Generate Cytoscape.js HTML visualization for a single tree."""
        cytoscape_data = self._convert_to_cytoscape_json()

        html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon"
            href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🍂</text></svg>">
        <title>DFS Tree {tree_index}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.33.0/cytoscape.min.js"></script>
        <!-- Layout extensions -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                height: 100vh;
                overflow: hidden;
                background: #f5f5f5;
                position: relative;
            }}

            #cy {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: #ffffff;
                transition: right 0.3s ease;
            }}

            #cy.sidebar-open {{
                right: 350px;
            }}

            #sidebar {{
                position: fixed;
                top: 0;
                right: 0;
                width: 350px;
                height: 100vh;
                background: #fafafa;
                border-left: 1px solid #ddd;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 20px;
                box-shadow: -2px 0 8px rgba(0,0,0,0.05);
                transform: translateX(0);
                transition: transform 0.3s ease;
                z-index: 100;
            }}

            #sidebar.closed {{
                transform: translateX(100%);
            }}

            #sidebar h2 {{
                font-size: 18px;
                margin-bottom: 15px;
                color: #333;
                border-bottom: 2px solid #4A90E2;
                padding-bottom: 8px;
            }}

            #sidebar h3 {{
                font-size: 14px;
                margin-top: 15px;
                margin-bottom: 8px;
                color: #666;
                font-weight: 600;
            }}

            #sidebar p {{
                font-size: 13px;
                line-height: 1.6;
                color: #555;
                margin-bottom: 8px;
                word-wrap: break-word;
            }}

            #sidebar .node-status {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            #sidebar .status-prefix {{ background: #E3F2FD; color: #1976D2; }}
            #sidebar .status-explored {{ background: #FFF3E0; color: #E65100; }}
            #sidebar .status-done {{ background: #E8F5E9; color: #2E7D32; }}
            #sidebar .status-failed {{ background: #FFEBEE; color: #C62828; }}

            .controls {{
                position: absolute;
                top: 15px;
                left: 15px;
                z-index: 1000;
                background: white;
                padding: 12px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                max-width: 200px;
            }}

            .controls button {{
                width: 100%;
                margin: 3px 0;
                padding: 8px 14px;
                border: none;
                background: #4A90E2;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: background 0.2s;
            }}

            .controls button:hover {{
                background: #357ABD;
            }}

            .sidebar-toggle {{
                position: absolute;
                top: 55px;
                right: 415px;
                z-index: 1001;
                background: white;
                padding: 10px 14px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                cursor: pointer;
                font-size: 18px;
                transition: right 0.3s ease;
                border: none;
                color: #4A90E2;
            }}

            .sidebar-toggle:hover {{
                background: #f0f0f0;
            }}

            .sidebar-toggle.sidebar-closed {{
                right: 15px;
            }}

            .back-link {{
                position: absolute;
                top: 15px;
                right: 415px;
                z-index: 1000;
                background: white;
                padding: 10px 16px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                text-decoration: none;
                color: #4A90E2;
                font-weight: 500;
                font-size: 13px;
                transition: right 0.3s ease;
            }}

            .back-link:hover {{
                background: #f0f0f0;
            }}

            .back-link.sidebar-closed {{
                right: 65px;
            }}

            #info {{
                margin-top: 20px;
                padding: 12px;
                background: #fff;
                border-radius: 4px;
                border-left: 3px solid #4A90E2;
                font-size: 12px;
                color: #666;
            }}

            .legend {{
                position: absolute;
                bottom: 15px;
                left: 15px;
                z-index: 1000;
                background: white;
                padding: 15px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                max-width: 220px;
                font-size: 12px;
            }}

            .legend h3 {{
                font-size: 13px;
                margin-bottom: 10px;
                color: #333;
                font-weight: 600;
                border-bottom: 2px solid #4A90E2;
                padding-bottom: 5px;
            }}

            .legend-section {{
                margin-bottom: 12px;
            }}

            .legend-section:last-child {{
                margin-bottom: 0;
            }}

            .legend-section h4 {{
                font-size: 11px;
                color: #666;
                margin-bottom: 5px;
                font-weight: 600;
                text-transform: uppercase;
            }}

            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }}

            .legend-item:last-child {{
                margin-bottom: 0;
            }}

            .legend-symbol {{
                width: 20px;
                height: 20px;
                margin-right: 8px;
                border: 2px solid;
                display: inline-block;
                flex-shrink: 0;
            }}

            .legend-symbol.circle {{
                border-radius: 50%;
            }}

            .legend-symbol.diamond {{
                transform: rotate(45deg);
                width: 16px;
                height: 16px;
                margin-right: 12px;
            }}

            .legend-symbol.prefix {{
                background-color: #90CAF9;
                border-color: #1976D2;
            }}

            .legend-symbol.explored {{
                background-color: #FFB74D;
                border-color: #E65100;
            }}

            .legend-symbol.done {{
                background-color: #81C784;
                border-color: #2E7D32;
            }}

            .legend-symbol.failed {{
                background-color: #E57373;
                border-color: #C62828;
            }}

            .legend-line {{
                width: 30px;
                height: 2px;
                margin-right: 8px;
                position: relative;
            }}

            .legend-line.normal {{
                background-color: #757575;
            }}

            .legend-line.backtrack {{
                background: none;
                border-bottom: 2px dashed #F44336;
                height: 0;
                margin-top: 1px;
            }}

            .legend-line::after {{
                content: '';
                position: absolute;
                right: -5px;
                top: -3px;
                width: 0;
                height: 0;
                border-left: 5px solid;
                border-top: 4px solid transparent;
                border-bottom: 4px solid transparent;
            }}

            .legend-line.normal::after {{
                border-left-color: #757575;
            }}

            .legend-line.backtrack::after {{
                border-left-color: #F44336;
                top: -4px;
            }}

            .legend-text {{
                font-size: 11px;
                color: #555;
            }}


            .zoom-controls {{
                border-top: 1px solid #ddd;
                margin-top: 10px;
                padding-top: 10px;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}

            .zoom-slider {{
                width: 100%;
                height: 6px;
                border-radius: 3px;
                background: #ddd;
                outline: none;
                cursor: pointer;
                -webkit-appearance: none;
            }}

            .zoom-slider::-webkit-slider-thumb {{
                -webkit-appearance: none;
                appearance: none;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #4A90E2;
                cursor: pointer;
            }}

            .zoom-slider::-moz-range-thumb {{
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #4A90E2;
                cursor: pointer;
                border: none;
            }}

            .zoom-level {{
                text-align: center;
                font-size: 11px;
                color: #666;
                font-weight: 500;
            }}



        .fullscreen-btn {{
            position: fixed !important;
            bottom: 15px !important;
            right: 15px !important;
            z-index: 10000 !important;
            width: 40px !important;
            height: 40px !important;
            padding: 0 !important;
            margin: 0 !important;
            background: #4A90E2 !important;
            color: white !important;
            border: none !important;
            border-radius: 50% !important;
            font-size: 18px !important;
            cursor: pointer !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        .fullscreen-btn:hover {{
            background: #357ABD !important;
            transform: scale(1.1) !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
        }}

        body.fullscreen-mode {{
            background: #1a1a1a !important;
        }}

        /* Hide all UI but keep button and info visible */
        body.fullscreen-mode aside.closed {{
            display: none !important;
        }}

        body.fullscreen-mode aside:not(.closed) {{
            display: block !important;
        }}

        body.fullscreen-mode .controls,
        body.fullscreen-mode .back-link,
        body.fullscreen-mode .sidebar-toggle,
        body.fullscreen-mode .legend {{
            display: none !important;
        }}

        body.fullscreen-mode #cy {{
            height: 100vh !important;
            width: 100vw !important;
        }}

        body.fullscreen-mode .container,
        body.fullscreen-mode header,
        body.fullscreen-mode .content {{
            display: none !important;
        }}

        /* Fullscreen mode layout */
        body.fullscreen-mode {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }}

        body.fullscreen-mode #cy {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* Button state indicator */
        .fullscreen-btn.active {{
            background: #E74C3C !important;
        }}

        .fullscreen-btn.active:hover {{
            background: #C0392B !important;
        }}

        /* Ensure button stays visible in fullscreen */
        body.fullscreen-mode .fullscreen-btn {{
            display: flex !important;
        }}

        /* Sidebar styling in fullscreen - visible but minimal */
        body.fullscreen-mode aside {{
            width: 350px !important;
            right: 0 !important;
        }}

        body.fullscreen-mode aside h2 {{
            display: none !important;
        }}

        </style>
    </head>
    <body>
        <div id="cy" class="sidebar-open"></div>

        <div class="controls">
            <button id="fullscreen-toggle" class="fullscreen-btn" title="Toggle fullscreen mode (F)">F</button>

            <button id="fit-btn">🔍 Fit to Screen</button>
            <button id="dagre-layout">📊 Dagre Layout</button>
            <button id="breadth-layout">🌳 Breadthfirst</button>
            <button id="circle-layout">⭕ Circle Layout</button>
            <button id="reset-layout">🔄 Reset Positions</button>


            <div class="zoom-controls">
                <button id="zoom-in-btn">🔎+ Zoom In</button>
                <input type="range" id="zoom-slider" min="0.1" max="3" value="1" step="0.1" class="zoom-slider" title="Adjust zoom level">
                <button id="zoom-out-btn">🔎− Zoom Out</button>
                <span id="zoom-level" class="zoom-level">100%</span>
            </div>
        </div>

        <button class="sidebar-toggle" id="sidebar-toggle" title="Close Sidebar">◀</button>

        <a href="../tree_index.html" class="back-link" id="back-link">← Back to Index</a>

        <div class="legend">
            <h3>Legend</h3>

            <div class="legend-section">
                <h4>Node Types</h4>
                <div class="legend-item">
                    <span class="legend-symbol circle prefix"></span>
                    <span class="legend-text">Prefix</span>
                </div>
                <div class="legend-item">
                    <span class="legend-symbol circle explored"></span>
                    <span class="legend-text">Explored</span>
                </div>
                <div class="legend-item">
                    <span class="legend-symbol circle done"></span>
                    <span class="legend-text">Success</span>
                </div>
                <div class="legend-item">
                    <span class="legend-symbol circle failed"></span>
                    <span class="legend-text">Failed</span>
                </div>
            </div>

            <div class="legend-section">
                <h4>Leaf Nodes</h4>
                <div class="legend-item">
                    <span class="legend-symbol diamond done"></span>
                    <span class="legend-text">Success Leaf</span>
                </div>
                <div class="legend-item">
                    <span class="legend-symbol diamond failed"></span>
                    <span class="legend-text">Failed Leaf</span>
                </div>
            </div>

            <div class="legend-section">
                <h4>Edge Types</h4>
                <div class="legend-item">
                    <span class="legend-line normal"></span>
                    <span class="legend-text">Normal</span>
                </div>
                <div class="legend-item">
                    <span class="legend-line backtrack"></span>
                    <span class="legend-text">Backtrack</span>
                </div>
            </div>
        </div>

        <div id="sidebar">
            <h2>Node Information</h2>
            <p style="color: #999; font-style: italic;">Click on a node to see details</p>
            <div id="info">
                <p><strong>Tip:</strong> Drag nodes to reposition them. Use mouse wheel to zoom. Drag background to pan.</p>
            </div>
        </div>

        <script>
            // Cytoscape data
            const cytoscapeData = {json.dumps(cytoscape_data)};

            // Initialize Cytoscape
            const cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: cytoscapeData.elements,

                style: [
                    // Node styles
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'text-wrap': 'wrap',
                            'text-max-width': '120px',
                            'font-size': '11px',
                            'font-weight': '500',
                            'width': '50px',
                            'height': '50px',
                            'border-width': 2,
                            'border-color': '#666',
                            'background-opacity': 0.9,
                            'text-outline-width': 2,
                            'text-outline-color': '#fff',
                        }}
                    }},
                    {{
                        selector: 'node.prefix',
                        style: {{
                            'background-color': '#90CAF9',
                            'border-color': '#1976D2',
                        }}
                    }},
                    {{
                        selector: 'node.explored',
                        style: {{
                            'background-color': '#FFB74D',
                            'border-color': '#E65100',
                        }}
                    }},
                    {{
                        selector: 'node.done',
                        style: {{
                            'background-color': '#81C784',
                            'border-color': '#2E7D32',
                        }}
                    }},
                    {{
                        selector: 'node.failed',
                        style: {{
                            'background-color': '#E57373',
                            'border-color': '#C62828',
                        }}
                    }},
                    {{
                        selector: 'node.leaf',
                        style: {{
                            'shape': 'diamond',
                            'width': '65px',
                            'height': '65px',
                            'border-width': 3,
                            'font-size': '12px',
                            'font-weight': '700',
                        }}
                    }},
                    {{
                        selector: 'node:selected',
                        style: {{
                            'border-width': 4,
                            'border-color': '#FF9800',
                            'overlay-opacity': 0.2,
                            'overlay-color': '#FF9800',
                        }}
                    }},

                    // Edge styles
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': '#999',
                            'target-arrow-color': '#999',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'arrow-scale': 1.2,
                        }}
                    }},
                    {{
                        selector: 'edge.normal',
                        style: {{
                            'line-color': '#757575',
                            'target-arrow-color': '#757575',
                        }}
                    }},
                    {{
                        selector: 'edge.backtrack',
                        style: {{
                            'line-color': '#F44336',
                            'target-arrow-color': '#F44336',
                            'line-style': 'dashed',
                            'width': 2.5,
                        }}
                    }},
                    {{
                        selector: 'edge:selected',
                        style: {{
                            'line-color': '#FF9800',
                            'target-arrow-color': '#FF9800',
                            'width': 3,
                        }}
                    }}
                ],

                layout: {{
                    name: 'dagre',
                    rankDir: 'TB',
                    nodeSep: 80,
                    rankSep: 100,
                    animate: false,
                }},

                // Enable interactions
                minZoom: 0.2,
                maxZoom: 3,
                wheelSensitivity: 0.2,
            }});


            // Zoom controls
            const zoomInBtn = document.getElementById('zoom-in-btn');
            const zoomOutBtn = document.getElementById('zoom-out-btn');
            const zoomSlider = document.getElementById('zoom-slider');
            const zoomLevel = document.getElementById('zoom-level');

            function updateZoomLevel(zoomValue) {{
                cy.zoom(parseFloat(zoomValue));
                zoomLevel.textContent = Math.round(zoomValue * 100) + '%';
            }}

            zoomInBtn.addEventListener('click', () => {{
                const newZoom = Math.min(cy.zoom() * 1.2, 3);
                cy.zoom(newZoom);
                zoomSlider.value = newZoom;
                zoomLevel.textContent = Math.round(newZoom * 100) + '%';
            }});

            zoomOutBtn.addEventListener('click', () => {{
                const newZoom = Math.max(cy.zoom() / 1.2, 0.1);
                cy.zoom(newZoom);
                zoomSlider.value = newZoom;
                zoomLevel.textContent = Math.round(newZoom * 100) + '%';
            }});

            zoomSlider.addEventListener('input', (e) => {{
                updateZoomLevel(e.target.value);
            }});


            // Sidebar toggle functionality
            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebar-toggle');
            const backLink = document.getElementById('back-link');
            const cyDiv = document.getElementById('cy');
            let sidebarOpen = true;

            function openSidebar() {{
                sidebarOpen = true;
                sidebar.classList.remove('closed');
                cyDiv.classList.add('sidebar-open');
                sidebarToggle.classList.remove('sidebar-closed');
                backLink.classList.remove('sidebar-closed');
                sidebarToggle.innerHTML = '◀';
                sidebarToggle.title = 'Close Sidebar';

                setTimeout(function() {{
                    cy.resize();
                    cy.fit(null, 50);
                }}, 350);
            }}

            function closeSidebar() {{
                sidebarOpen = false;
                sidebar.classList.add('closed');
                cyDiv.classList.remove('sidebar-open');
                sidebarToggle.classList.add('sidebar-closed');
                backLink.classList.add('sidebar-closed');
                sidebarToggle.innerHTML = '▶';
                sidebarToggle.title = 'Open Sidebar';

                setTimeout(function() {{
                    cy.resize();
                    cy.fit(null, 50);
                }}, 350);
            }}

            sidebarToggle.addEventListener('click', function() {{
                if (sidebarOpen) {{
                    closeSidebar();
                }} else {{
                    openSidebar();
                }}
            }});

            // Node click handler - update sidebar and open if closed
            cy.on('tap', 'node', function(evt) {{
                const node = evt.target;
                const data = node.data();

                const statusClass = 'status-' + data.status;
                const statusLabel = data.status.charAt(0).toUpperCase() + data.status.slice(1);

                let html = '<h2>Node: ' + data.id + '</h2>';
                html += '<p><span class="node-status ' + statusClass + '">' + statusLabel + '</span></p>';
                html += '<h3>Action Text</h3>';
                html += '<p>' + (data.full_text || 'N/A') + '</p>';
                html += '<h3>State</h3>';
                html += '<p>' + (data.state || 'N/A') + '</p>';
                html += '<h3>Properties</h3>';
                html += '<p><strong>Depth:</strong> ' + data.depth + ' (exploration sequence)</p>';
                html += '<p><strong>DFS Appearance Order:</strong> ' + data.appearance_order + '</p>';
                html += '<p><strong>Leaf Node:</strong> ' + (data.is_leaf ? 'Yes' : 'No') + '</p>';

                if (data.backtrack_reason) {{
                    html += '<h3>Backtrack Reason</h3>';
                    html += '<p>' + data.backtrack_reason + '</p>';
                }}

                // Show connections
                const outgoing = node.outgoers('edge').length;
                const incoming = node.incomers('edge').length;
                html += '<h3>Connections</h3>';
                html += '<p><strong>Incoming edges:</strong> ' + incoming + '</p>';
                html += '<p><strong>Outgoing edges:</strong> ' + outgoing + '</p>';

                sidebar.innerHTML = html;

                // Open sidebar when clicking on node
                if (!sidebarOpen) {{
                    openSidebar();
                }}
            }});

            // Control buttons
            document.getElementById('fit-btn').addEventListener('click', function() {{
                cy.fit(null, 50);
            }});

            document.getElementById('dagre-layout').addEventListener('click', function() {{
                cy.layout({{
                    name: 'dagre',
                    rankDir: 'TB',
                    nodeSep: 80,
                    rankSep: 120,
                    animate: true,
                    animationDuration: 500,
                }}).run();
            }});

            document.getElementById('breadth-layout').addEventListener('click', function() {{
                cy.layout({{
                    name: 'breadthfirst',
                    directed: true,
                    spacingFactor: 1.8,
                    animate: true,
                    animationDuration: 500,
                }}).run();
            }});

            document.getElementById('circle-layout').addEventListener('click', function() {{
                cy.layout({{
                    name: 'circle',
                    spacingFactor: 1.5,
                    animate: true,
                    animationDuration: 500,
                }}).run();
            }});

            document.getElementById('reset-layout').addEventListener('click', function() {{
                cy.nodes().forEach(node => {{
                    const level = node.data('level');
                    const id = parseInt(node.id());
                    node.position({{
                        x: (id % 10) * 100 + 100,
                        y: level * 120 + 100
                    }});
                }});
            }});



            const fullscreenBtn = document.getElementById('fullscreen-toggle');
            const body = document.body;
            const sidebarTwo = document.querySelector('aside');

            function toggleFullscreen() {{
                body.classList.toggle('fullscreen-mode');
                fullscreenBtn.classList.toggle('active');

                if (body.classList.contains('fullscreen-mode')) {{
                    // Entering fullscreen mode - close sidebarTwo if open
                    if (sidebarOpen) {{
                        closeSidebar();
                    }}
                }}

                // Resize and redraw Cytoscape when entering/exiting fullscreen
                setTimeout(function() {{
                    cy.resize();
                    cy.fit();
                }}, 100);
            }}

            fullscreenBtn.addEventListener('click', toggleFullscreen);

            // Keyboard shortcut (F key)
            document.addEventListener('keydown', function(e) {{
                if ((e.key.toLowerCase() === 'f' || e.key.toLowerCase() === 'а') && !e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {{
                    const activeElement = document.activeElement;
                    if (activeElement.tagName !== 'INPUT' && activeElement.tagName !== 'TEXTAREA') {{
                        e.preventDefault();
                        toggleFullscreen();
                    }}
                }}
            }});

            closeSidebar();

            // Initial fit
            cy.fit(null, 50);


        </script>
    </body>
    </html>"""

        return html

    def _generate_index_page(
        self, tree_stats: list[dict], step_t: Optional[int] = None
    ) -> str:
        """Generate an index page with statistics and links to individual trees."""
        # Calculate mean statistics
        total_trees = len(tree_stats)
        mean_stats = {
            "leaves": sum(s["leaves"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
            "nodes": sum(s["total_nodes"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
            "prefix": sum(s["prefix"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
            "explored": sum(s["explored"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
            "success": sum(s["success"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
            "failed": sum(s["failed"] for s in tree_stats) / total_trees
            if total_trees > 0
            else 0,
        }

        stats_rows = []
        for stats in tree_stats:
            stats_rows.append(f'''
                <tr>
                    <td data-value="{stats["tree_index"]}">{stats["tree_index"]}</td>
                    <td data-value="{stats["leaves"]}">{stats["leaves"]}</td>
                    <td data-value="{stats["total_nodes"]}">{stats["total_nodes"]}</td>
                    <td data-value="{stats["prefix"]}">{stats["prefix"]}</td>
                    <td data-value="{stats["explored"]}">{stats["explored"]}</td>
                    <td data-value="{stats["success"]}" class="success-cell">{stats["success"]}</td>
                    <td data-value="{stats["failed"]}" class="failed-cell">{stats["failed"]}</td>
                    <td><a href="{stats["filename"]}" class="view-btn">View Tree</a></td>
                </tr>
            ''')

        stats_table = "\n".join(stats_rows)

        index_title = (
            "🌳 DFS Tree Exploration"
            if step_t is None
            else f"🌳 DFS Tree Exploration for T={step_t}"
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon"
        href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌳</text></svg>">
    <title>DFS Tree Exploration - Index</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        header p {{
            font-size: 16px;
            opacity: 0.95;
        }}

        .content {{
            padding: 40px;
        }}

        h2 {{
            font-size: 24px;
            margin-bottom: 25px;
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        th {{
            background: #f8f9fa;
            color: #495057;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 14px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            cursor: pointer;
            user-select: none;
            position: relative;
        }}

        th:hover {{
            background: #e9ecef;
        }}

        th.sortable:after {{
            content: ' ⇅';
            opacity: 0.5;
        }}

        th.sorted-asc:after {{
            content: ' ▲';
            opacity: 1;
        }}

        th.sorted-desc:after {{
            content: ' ▼';
            opacity: 1;
        }}

        td {{
            padding: 14px;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
            font-size: 14px;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        tr.mean-row {{
            background: #fff3cd;
            font-weight: 600;
            border-top: 3px solid #ffc107;
        }}

        tr.mean-row:hover {{
            background: #ffe69c;
        }}

        .success-cell {{
            color: #2E7D32;
            font-weight: 600;
        }}

        .failed-cell {{
            color: #C62828;
            font-weight: 600;
        }}

        .view-btn {{
            display: inline-block;
            padding: 8px 16px;
            background: #4A90E2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            font-size: 13px;
            transition: all 0.2s;
        }}

        .view-btn:hover {{
            background: #357ABD;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        .back-to-global {{
            position: absolute;
            top: 40px;
            right: 20px;
            z-index: 1000;
            background: white;
            padding: 10px 16px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            text-decoration: none;
            color: #4A90E2;
            font-weight: 500;
            font-size: 13px;
            transition: all 0.2s;
        }}
        .back-to-global:hover {{
            background: #f0f0f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .summary-card h3 {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .summary-card p {{
            font-size: 32px;
            font-weight: 700;
            color: #333;
        }}

        .summary-card.success {{
            background: linear-gradient(135deg, #81C784 0%, #66BB6A 100%);
        }}

        .summary-card.success h3,
        .summary-card.success p {{
            color: white;
        }}

        .summary-card.failed {{
            background: linear-gradient(135deg, #E57373 0%, #EF5350 100%);
        }}

        .summary-card.failed h3,
        .summary-card.failed p {{
            color: white;
        }}
    </style>
</head>
<body>
    <a href="../{self.folder_prefix}.html" class="back-to-global">← Back to Global Index</a>
    <div class="container">
        <header>
            <h1>{index_title}</h1>
            <p>Interactive visualization of depth-first search exploration trees</p>
        </header>

        <div class="content">
            <h2>📊 Overview</h2>
            <div class="summary">
                <div class="summary-card">
                    <h3>Total Trees</h3>
                    <p>{len(tree_stats)}</p>
                </div>
                <div class="summary-card">
                    <h3>Total Nodes</h3>
                    <p>{sum(s["total_nodes"] for s in tree_stats)}</p>
                </div>
                <div class="summary-card">
                    <h3>Total Edges</h3>
                    <p>{sum(s["total_edges"] for s in tree_stats)}</p>
                </div>
                <div class="summary-card success">
                    <h3>Success Paths</h3>
                    <p>{sum(s["success"] for s in tree_stats)}</p>
                </div>
                <div class="summary-card failed">
                    <h3>Failed Paths</h3>
                    <p>{sum(s["failed"] for s in tree_stats)}</p>
                </div>
            </div>

            <h2>🗂️ Tree Statistics (Click column headers to sort)</h2>
            <table id="stats-table">
                <thead>
                    <tr>
                        <th class="sortable" data-column="0">Tree #</th>
                        <th class="sortable" data-column="1">Leaves</th>
                        <th class="sortable" data-column="2">Nodes</th>
                        <th class="sortable" data-column="3">Prefix</th>
                        <th class="sortable" data-column="4">Explored</th>
                        <th class="sortable" data-column="5">Success</th>
                        <th class="sortable" data-column="6">Failed</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                    <tr class="mean-row">
                        <td>Mean</td>
                        <td>{mean_stats["leaves"]:.2f}</td>
                        <td>{mean_stats["nodes"]:.2f}</td>
                        <td>{mean_stats["prefix"]:.2f}</td>
                        <td>{mean_stats["explored"]:.2f}</td>
                        <td class="success-cell">{mean_stats["success"]:.2f}</td>
                        <td class="failed-cell">{mean_stats["failed"]:.2f}</td>
                        <td>-</td>
                    </tr>
                    {stats_table}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Table sorting functionality
        const table = document.getElementById('stats-table');
        const headers = table.querySelectorAll('th.sortable');
        const tbody = document.getElementById('table-body');
        const meanRow = tbody.querySelector('.mean-row');

        let currentSort = {{ column: -1, ascending: true }};

        headers.forEach(header => {{
            header.addEventListener('click', function() {{
                const column = parseInt(this.dataset.column);
                const ascending = currentSort.column === column ? !currentSort.ascending : true;

                sortTable(column, ascending);

                // Update header styles
                headers.forEach(h => {{
                    h.classList.remove('sorted-asc', 'sorted-desc');
                }});
                this.classList.add(ascending ? 'sorted-asc' : 'sorted-desc');

                currentSort = {{ column, ascending }};
            }});
        }});

        function sortTable(column, ascending) {{
            // Get all rows except the mean row
            const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.classList.contains('mean-row'));

            rows.sort((a, b) => {{
                const aValue = parseFloat(a.cells[column].dataset.value);
                const bValue = parseFloat(b.cells[column].dataset.value);

                if (ascending) {{
                    return aValue - bValue;
                }} else {{
                    return bValue - aValue;
                }}
            }});

            // Remove all rows
            rows.forEach(row => tbody.removeChild(row));

            // Re-add sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }}

    </script>
</body>
</html>"""

        return html
