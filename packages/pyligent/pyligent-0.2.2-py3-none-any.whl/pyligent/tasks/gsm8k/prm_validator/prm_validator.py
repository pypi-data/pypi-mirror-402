"""
PRM-backed validator that scores reasoning steps with a Process Reward Model.
"""

from typing import Optional

from loguru import logger

from pyligent.core.action import NodeAction
from pyligent.core.path import PathContext
from pyligent.core.validator import HandlerResult
from pyligent.tasks.gsm8k.prm_validator.scorer import PRMScorer
from pyligent.tasks.gsm8k.validator import GSM8KValidator


class PRMGSM8KValidator(GSM8KValidator):
    """
    GSM8K validator that delegates NodeAction checks to a PRM score.

    A NodeAction is accepted only if the PRM score for that step exceeds the threshold.
    DoneAction validation (answer checking) is inherited from GSM8KValidator.
    """

    def __init__(
        self,
        expected_answers: Optional[dict[str, str]] = None,
        eps: float = 1e-6,
        threshold: float = 0.1,
        model_name: str = "Qwen/Qwen2.5-Math-PRM-7B",
        device: str = "auto",
        scorer: Optional[PRMScorer] = None,
    ):
        self.threshold = threshold
        self._score_cache: dict[tuple[int, str], float] = {}
        self.prm_scorer = scorer or PRMScorer(model_name=model_name, device=device)
        logger.info(
            f"Initialized PRM-backed validator with model '{model_name}' "
            f"(threshold={threshold})"
        )
        super().__init__(expected_answers=expected_answers, eps=eps)

    @staticmethod
    def _extract_question_and_steps(context: PathContext) -> tuple[str, list[str]]:
        question = ""
        steps: list[str] = []
        for idx, node in enumerate(context.nodes):
            action = node.action
            if isinstance(action, NodeAction):
                text = action.text.strip()
                if idx == 0 and not question:
                    question = text
                else:
                    steps.append(text)
        return question, steps

    def _invalid_node_content_handler(
        self, action: NodeAction, context: PathContext
    ) -> HandlerResult:
        cache_key = (context.hash_value, action.text.strip())
        if cache_key in self._score_cache:
            score = self._score_cache[cache_key]
        else:
            question, steps = self._extract_question_and_steps(context)
            if not question:
                return HandlerResult(False, "Missing question in context for PRM scoring")

            try:
                score = self.prm_scorer.step_reward(
                    question, "\n".join(steps), action.text.strip()
                )
            except Exception as exc:  # pragma: no cover - depends on external model
                logger.exception("PRM scoring failed")
                return HandlerResult(False, f"PRM scoring failed: {exc}")

            self._score_cache[cache_key] = score

        if score > self.threshold:
            return HandlerResult(True)
        return HandlerResult(
            False,
            f"PRM score {score:.3f} <= threshold {self.threshold:.3f}",
        )
