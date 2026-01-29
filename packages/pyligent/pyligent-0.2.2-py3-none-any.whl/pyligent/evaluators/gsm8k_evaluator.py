"""
GSM8K-specific evaluator implementation.
"""

import re
from typing import Any, Optional

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.evaluator import BaseEvaluator, EvaluationConfig
from pyligent.tasks.gsm8k.adapter import GSM8KAdapter


class GSM8KEvaluator(BaseEvaluator):
    """Evaluator for GSM8K mathematical reasoning dataset."""

    # Regex patterns for parsing actions
    RE_NODE = re.compile(r"<node>(\d+)\s+(.*?)\s*</node>", re.S)
    RE_BACK = re.compile(r"<backtrack>(\d+)</backtrack>")
    RE_DONE = re.compile(r"<done>\s*(.*?)\s*</done>", re.S)

    def __init__(self, config: EvaluationConfig):
        """Initialize GSM8K evaluator."""
        super().__init__(config)
        self.adapter = GSM8KAdapter()

    def load_dataset(self) -> list[dict[str, Any]]:
        """Load GSM8K dataset using existing adapter."""
        eval_cfg = self.config.evaluation
        split = eval_cfg.get("split", "test")

        # Load golden paths from adapter
        golden_paths = self.adapter.load_golden_paths(split=split)

        # Convert to evaluation format
        examples = []
        for gp in golden_paths:
            question = gp.nodes[0].action.text
            expected = gp.nodes[-1].action.text

            examples.append(
                {
                    "question": question,
                    "expected": expected,
                }
            )

        return examples

    def parse_action(self, text: str) -> Optional[Action]:
        """Parse generated text into an Action object."""
        # Try to match node
        if m := self.RE_NODE.search(text):
            node_id = int(m.group(1))
            content = m.group(2).strip()
            return NodeAction(node_id, content)

        # Try to match backtrack
        if m := self.RE_BACK.search(text):
            node_id = int(m.group(1))
            return BacktrackAction(node_id)

        # Try to match done
        if m := self.RE_DONE.search(text):
            answer = m.group(1).strip()
            return DoneAction(answer)

        return None

    def extract_answer(self, action: Action) -> Optional[str]:
        """Extract final answer if action is DoneAction."""
        if isinstance(action, DoneAction):
            return action.text
        return None

    def compare_answers(self, predicted: str, expected: str) -> bool:
        """
        Compare predicted and expected answers.

        For GSM8K, we do case-insensitive string matching.
        Could be extended to parse numeric values.
        """
        return predicted.strip().lower() == expected.strip().lower()
