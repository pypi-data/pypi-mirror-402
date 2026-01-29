import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pyligent.common.dataset_implementations import BasicDataset
from pyligent.core import DiligentDataset
from pyligent.core.action import Action, DoneAction, NodeAction
from pyligent.core.path import GoldPath, Node, PathContext
from pyligent.core.state import TextConcatStateEngine


class BlocksworldAdapter:
    def __init__(self, dataset_path: Path):
        self.state_engine = TextConcatStateEngine()
        self.path = dataset_path

    @staticmethod
    def split_steps(text: str) -> List[str]:
        return text.split("\n")

    @staticmethod
    def format_query(text: str) -> str:
        to_find = "As initial conditions I have that, "
        state_start = text.rfind(to_find) + len(to_find)
        text = text[state_start:]

        to_find = "\nMy goal is to have that "
        goal_start = text.rfind(to_find)
        goal_end = text.rfind("\n\nMy plan is as follows:")
        query = f"Blocks state: {text[:goal_start].strip()}\nGoal: {text[goal_start + len(to_find) : goal_end].strip()}"
        return query

    def load_golden_paths_raw(self) -> List[Dict]:
        with open(self.path, "r") as f:
            ds = json.load(f)["instances"]

        golden_paths_raw = []
        for ex in ds:
            q = self.format_query(ex["query"])
            final_answer = ex["ground_truth_plan"].strip()
            steps = self.split_steps(final_answer)

            # Skip if no valid answer or no steps
            if len(steps) < 1:
                continue

            golden_paths_raw.append(
                {"question": q, "steps": steps, "final_answer": final_answer}
            )

        return golden_paths_raw

    def create_gold_path(self, raw_path: Dict) -> GoldPath:
        """
        Convert a raw path dictionary into a GoldPath object.

        Args:
            raw_path: Dictionary with 'question', 'steps', and 'final_answer'

        Returns:
            GoldPath object with proper Node structure
        """
        question = raw_path["question"]
        steps = raw_path["steps"]
        final_answer = raw_path["final_answer"]

        nodes = []
        node_id = 0

        # Root node (node_id=0): the question
        root_action = NodeAction(node_id, question)
        root_node = Node(parent=None, action=root_action)
        nodes.append(root_node)
        node_id += 1

        # Add all reasoning steps as nodes
        parent = root_node
        for step in steps:
            action = NodeAction(node_id, step)
            node = Node(
                parent=parent,
                action=action,
                state=self.state_engine.reduce(parent.state, action),
            )
            # parent.add_child(node)
            nodes.append(node)
            parent = node
            node_id += 1

        # Add final DoneAction node
        done_action = DoneAction(final_answer)
        done_node = Node(
            parent=parent,
            action=done_action,
            state=self.state_engine.reduce(parent.state, action),
        )
        # parent.add_child(done_node)
        nodes.append(done_node)

        # Create and return GoldPath
        gold_path = GoldPath(nodes=nodes)
        return gold_path

    def load_golden_paths(self) -> List[GoldPath]:
        raw_paths = self.load_golden_paths_raw()
        gold_paths = [self.create_gold_path(rp) for rp in raw_paths]
        return gold_paths

    def create_phase_pairs_from_gold_path(
        self,
        gold_path: GoldPath,
        t: int,
    ) -> List[Tuple[PathContext, Action]]:
        # GoldPath must have at least t+1 nodes (to have t remaining)
        if len(gold_path) < t + 1:
            return []

        # For phase t, we want to predict action at position len(gold_path) - t
        # The prefix is all nodes before that position
        prefix_end = len(gold_path.nodes) - t
        prefix_nodes = gold_path.nodes[:prefix_end]
        target_action = gold_path.nodes[prefix_end].action

        # Create PathContext from prefix
        context = PathContext(nodes=prefix_nodes)

        return [(context, target_action)]

    def create_phase_pairs(
        self,
        gold_paths: List[GoldPath],
        t: int,
    ) -> List[Tuple[PathContext, Action]]:
        pairs = []
        for gold_path in gold_paths:
            pairs.extend(self.create_phase_pairs_from_gold_path(gold_path, t))
        return pairs

    def build_diligent_dataset(
        self,
        t: Optional[int] = None,
        t_values: Optional[List[int]] = None,
        check_unique: bool = True,
        gold_paths: Optional[List[GoldPath]] = None,
    ) -> DiligentDataset:
        # Load golden paths if not provided
        if gold_paths is None:
            gold_paths = self.load_golden_paths()

        # Determine which phases to include
        if t is not None and t_values is not None:
            raise ValueError("Cannot specify both 't' and 't_values'")

        if t is not None:
            phases = [t]
        elif t_values is not None:
            phases = t_values
        else:
            # Default: include multiple phases
            phases = [1, 2, 3, 4, 5]

        # Create pairs for all phases
        all_pairs = []
        for phase in phases:
            phase_pairs = self.create_phase_pairs(gold_paths, phase)
            all_pairs.extend(phase_pairs)
            print(f"Phase {phase}: {len(phase_pairs)} pairs")

        # Create DiligentDataset
        dataset = BasicDataset(gold_pairs=all_pairs, check_unique=check_unique)

        return dataset

    def save_golden_paths(self, output_path: str):
        raw_paths = self.load_golden_paths_raw()

        with open(output_path, "w") as f:
            for rec in raw_paths:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"Saved {len(raw_paths)} golden paths to {output_path}")

    def save_phase_dataset(self, output_path: str, t: int = 1):
        # Load golden paths as GoldPath objects
        gold_paths = self.load_golden_paths()

        examples = []
        for gold_path in gold_paths:
            # Get pairs for this phase
            pairs = self.create_phase_pairs_from_gold_path(gold_path, t)

            for context, action in pairs:
                context_str = str(context)
                target_str = str(action)

                examples.append({"context": context_str, "target": target_str})

        with open(output_path, "w") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        print(f"Saved {len(examples)} phase {t} examples to {output_path}")


# ============================================================================
# Example Usage Functions
# ============================================================================


def example_basic_usage(ds_path: Path):
    """Example 1: Create a DiligentDataset for a single phase."""
    print("=== Example 1: Single Phase Dataset ===")
    adapter = BlocksworldAdapter(ds_path)

    # Create dataset for phase 3 (3 steps remaining)
    dataset = adapter.build_diligent_dataset(t=3, check_unique=True)

    print(f"\nCreated dataset with {len(dataset)} examples")

    # Show first example
    if len(dataset) > 0:
        context, action = dataset.pairs[0]
        print("\nFirst example:")
        print(f"  Context: {context}")
        print(f"  Target action: {action}")

    return dataset


def example_with_gold_paths(ds_path: Path):
    """Example 2: Work directly with GoldPath objects."""
    print("\n=== Example 2: Working with GoldPath Objects ===")
    adapter = BlocksworldAdapter(ds_path)

    # Load as GoldPath objects
    gold_paths = adapter.load_golden_paths()
    print(f"Loaded {len(gold_paths)} GoldPath objects")

    # Inspect first gold path
    if gold_paths:
        first_gold = gold_paths[0]
        print(f"\nFirst GoldPath (length={len(first_gold)}):")
        print(f"  {first_gold}")
        print("\nNodes breakdown:")
        for i, node in enumerate(first_gold.nodes):
            print(f"    {i}. {node.action}")

    # Create dataset from these gold paths
    dataset = adapter.build_diligent_dataset(
        t_values=[1, 2], gold_paths=gold_paths, check_unique=True
    )
    print(f"\nCreated dataset with {len(dataset)} examples from gold paths")

    return gold_paths, dataset


def example_multi_phase(ds_path: Path):
    """Example 3: Create a DiligentDataset with multiple phases."""
    print("\n=== Example 3: Multi-Phase Dataset ===")
    adapter = BlocksworldAdapter(ds_path)

    # Create dataset combining phases 1, 2, 3
    dataset = adapter.build_diligent_dataset(t_values=[1, 2, 3], check_unique=True)

    print(f"\nCreated multi-phase dataset with {len(dataset)} examples")
    return dataset


def example_save_files(ds_path: Path):
    """Example 4: Save intermediate files using proper class representations."""
    print("\n=== Example 4: Save Intermediate Files ===")
    adapter = BlocksworldAdapter(ds_path)

    # Save golden paths
    adapter.save_golden_paths("train_golden.jsonl")

    # Save phase datasets with proper string representations
    for phase in [1, 2, 3]:
        adapter.save_phase_dataset(f"train_phase_{phase}.jsonl", t=phase)

    print("\nAll intermediate files saved with proper class string representations")


def example_phase_breakdown(ds_path: Path):
    """Example 5: Show how phases work with a specific GoldPath."""
    print("\n=== Example 5: Phase Breakdown with GoldPath ===")
    adapter = BlocksworldAdapter(ds_path)

    gold_paths = adapter.load_golden_paths()

    # Find a gold path with at least 5 nodes
    example_gold = None
    for gp in gold_paths:
        if len(gp) >= 5:
            example_gold = gp
            break

    if not example_gold:
        print("No gold path with 5+ nodes found")
        return

    print(f"Example GoldPath (length={len(example_gold)}):")
    print(f"  {example_gold}")

    # Show what each phase looks like with proper string representations
    for t in [1, 2, 3]:
        pairs = adapter.create_phase_pairs_from_gold_path(example_gold, t)
        if pairs:
            context, action = pairs[0]
            print(f"\n--- Phase t={t} (predict with {t} steps remaining) ---")
            print(f"Context: {context}")
            print(f"Target: {action}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Blocksworld adapter examples")
    parser.add_argument(
        "path", type=Path, help="Path to the Blocksword dataset in PlanBench format"
    )
    args = parser.parse_args()
    # Run all examples
    example_basic_usage(args.path)
    example_with_gold_paths(args.path)
    example_multi_phase(args.path)
    example_save_files(args.path)
    example_phase_breakdown(args.path)

    print("\nDone")
