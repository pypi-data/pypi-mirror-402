import json
import re
from typing import Optional

from datasets import load_dataset

from pyligent.common.dataset_implementations import BasicDataset
from pyligent.core import DiligentDataset
from pyligent.core.action import Action, DoneAction, NodeAction
from pyligent.core.path import GoldPath, Node, PathContext
from pyligent.core.state import TextConcatStateEngine

AFTER_HASHES_RE = re.compile(r"####\s*(.*)")


class GSM8KAdapter:
    """
    Adapter to convert GSM8K dataset into DiligentDataset format.
    Combines the logic from build_golden_paths.py and build_phase_dataset.py.
    """

    def __init__(
        self,
        dataset_name: str = "openai/gsm8k",
        dataset_config: str = "main",
    ):
        """
        Initialize the GSM8K adapter.

        Args:
            dataset_name: HuggingFace dataset name
            dataset_config: Dataset configuration
        """
        self.state_engine = TextConcatStateEngine()
        self.dataset_name = dataset_name
        self.dataset_config = dataset_config

    @staticmethod
    def split_steps(text: str) -> list[str]:
        """
        Split the GSM8K answer text into individual reasoning steps.

        Args:
            text: Raw answer text from GSM8K

        Returns:
            list of reasoning steps
        """
        # Normalize line breaks and strip calculator annotations
        text = text.replace("\r", "\n").strip()
        text = re.sub(r"<<.*?>>", "", text, flags=re.DOTALL)

        # Split by newlines
        parts = re.split("\n", text)
        steps = [p.strip() for p in parts if p and not p.isspace()]

        # Drop any standalone answer line (starts with ####)
        steps = [s for s in steps if s and not s.startswith("####")]

        return steps

    @staticmethod
    def extract_final_answer(text: str) -> Optional[str]:
        """
        Extract the final answer after '####' marker.

        Args:
            text: Raw answer text from GSM8K

        Returns:
            Final answer string or None
        """
        m = AFTER_HASHES_RE.search(text)
        if not m:
            return None
        return m.group(1).strip()

    def load_golden_paths_raw(self, split: str = "train") -> list[dict]:
        """
        Load and process GSM8K data into raw golden path format (dictionaries).

        Args:
            split: Dataset split ('train' or 'test')

        Returns:
            list of raw path dictionaries with question, steps, and final_answer
        """
        ds = load_dataset(
            self.dataset_name,
            self.dataset_config,
            split=split,
        )

        golden_paths_raw = []
        for ex in ds:
            # TODO: Check
            q = ex["question"].strip()  # type: ignore
            a = ex["answer"].strip()  # type: ignore

            steps = self.split_steps(a)
            final_answer = self.extract_final_answer(a)

            # Skip if no valid answer or no steps
            if final_answer is None or len(steps) < 1:
                continue

            golden_paths_raw.append(
                {
                    "question": q,
                    "steps": steps,
                    "final_answer": final_answer,
                }
            )

        return golden_paths_raw

    def create_gold_path(self, raw_path: dict) -> GoldPath:
        """
        Convert a raw path dictionary into a GoldPath object.

        Args:
            raw_path: dictionary with 'question', 'steps', and 'final_answer'

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
        root_node = Node(parent=None, action=root_action, state=question)
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

    def load_golden_paths(self, split: str = "train") -> list[GoldPath]:
        """
        Load GSM8K data as GoldPath objects.

        Args:
            split: Dataset split ('train' or 'test')

        Returns:
            list of GoldPath objects
        """
        raw_paths = self.load_golden_paths_raw(split)
        gold_paths = [self.create_gold_path(rp) for rp in raw_paths]
        return gold_paths

    def create_phase_pairs_from_gold_path(
        self,
        gold_path: GoldPath,
        t: int,
    ) -> list[tuple[PathContext, Action]]:
        """
        Create training pairs from a GoldPath for phase t.

        In phase t, the model learns to predict the next action when
        exactly t steps remain to reach the done node.

        Args:
            gold_path: GoldPath object
            t: Phase number (number of remaining steps to completion)

        Returns:
            list of (PathContext, Action) tuples
        """
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
        gold_paths: list[GoldPath],
        t: int,
    ) -> list[tuple[PathContext, Action]]:
        """
        Convert golden paths into (PathContext, Action) pairs for phase t.

        Args:
            gold_paths: list of GoldPath objects
            t: Phase number (number of remaining steps to completion)

        Returns:
            list of (PathContext, Action) tuples for DiligentDataset
        """
        pairs = []
        for gold_path in gold_paths:
            pairs.extend(self.create_phase_pairs_from_gold_path(gold_path, t))
        return pairs

    def build_diligent_dataset(
        self,
        split: str = "train",
        t: Optional[int] = None,
        t_values: Optional[list[int]] = None,
        check_unique: bool = True,
        gold_paths: Optional[list[GoldPath]] = None,
    ) -> DiligentDataset:
        """
        Build a complete DiligentDataset from GSM8K.

        Args:
            split: Dataset split ('train' or 'test')
            t: Single phase value (mutually exclusive with t_values)
            t_values: list of phase values to combine (mutually exclusive with t)
            check_unique: Whether to filter duplicate pairs
            gold_paths: Pre-loaded GoldPath objects (optional, will load if None)

        Returns:
            DiligentDataset ready for training
        """
        # Load golden paths if not provided
        if gold_paths is None:
            gold_paths = self.load_golden_paths(split)

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

    def save_golden_paths(self, output_path: str, split: str = "train"):
        """
        Save golden paths to JSONL file (compatible with build_golden_paths.py).

        Args:
            output_path: Path to output JSONL file
            split: Dataset split to save
        """
        raw_paths = self.load_golden_paths_raw(split)

        with open(output_path, "w") as f:
            for rec in raw_paths:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"Saved {len(raw_paths)} golden paths to {output_path}")

    def save_phase_dataset(self, output_path: str, split: str = "train", t: int = 1):
        """
        Save phase dataset to JSONL file using proper class string representations.

        Args:
            output_path: Path to output JSONL file
            split: Dataset split
            t: Phase number
        """
        # Load golden paths as GoldPath objects
        gold_paths = self.load_golden_paths(split)

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


def example_basic_usage():
    """Example 1: Create a DiligentDataset for a single phase."""
    print("=== Example 1: Single Phase Dataset ===")
    adapter = GSM8KAdapter()

    # Create dataset for phase 3 (3 steps remaining)
    dataset = adapter.build_diligent_dataset(split="train", t=3, check_unique=True)

    print(f"\nCreated dataset with {len(dataset)} examples")

    # Show first example
    if len(dataset) > 0:
        context, action = dataset.pairs[0]
        print("\nFirst example:")
        print(f"  Context: {context}")
        print(f"  Target action: {action}")

    return dataset


def example_with_gold_paths():
    """Example 2: Work directly with GoldPath objects."""
    print("\n=== Example 2: Working with GoldPath Objects ===")
    adapter = GSM8KAdapter()

    # Load as GoldPath objects
    gold_paths = adapter.load_golden_paths(split="train")
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


def example_multi_phase():
    """Example 3: Create a DiligentDataset with multiple phases."""
    print("\n=== Example 3: Multi-Phase Dataset ===")
    adapter = GSM8KAdapter()

    # Create dataset combining phases 1, 2, 3
    dataset = adapter.build_diligent_dataset(
        split="train", t_values=[1, 2, 3], check_unique=True
    )

    print(f"\nCreated multi-phase dataset with {len(dataset)} examples")
    return dataset


def example_save_files():
    """Example 4: Save intermediate files using proper class representations."""
    print("\n=== Example 4: Save Intermediate Files ===")
    adapter = GSM8KAdapter()

    # Save golden paths
    adapter.save_golden_paths("train_golden.jsonl", split="train")

    # Save phase datasets with proper string representations
    for phase in [1, 2, 3]:
        adapter.save_phase_dataset(f"train_phase_{phase}.jsonl", split="train", t=phase)

    print("\nAll intermediate files saved with proper class string representations")


def example_phase_breakdown():
    """Example 5: Show how phases work with a specific GoldPath."""
    print("\n=== Example 5: Phase Breakdown with GoldPath ===")
    adapter = GSM8KAdapter()

    gold_paths = adapter.load_golden_paths(split="train")

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
    # Run all examples
    example_basic_usage()
    example_with_gold_paths()
    example_multi_phase()
    example_save_files()
    example_phase_breakdown()

    print("\nDone")
