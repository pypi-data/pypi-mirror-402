import re

from pyligent.core import Validator
from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.path import PathContext
from pyligent.core.validator import HandlerResult
from pyligent.tasks.prime.state import PrimeState


class PrimeValidator(Validator):
    _int_re = r"^\+?[1-9]\d*$"

    def _basic_integer_handler(
        self, action: Action, context: PathContext
    ) -> HandlerResult:
        if isinstance(action, BacktrackAction):
            return HandlerResult(True, "")

        return HandlerResult(
            bool(re.match(self._int_re, action.text)),
            f"Action should be single integer. Got {action.text}",
        )

    def _prime_logic_handler(self, action: Action, context: PathContext) -> HandlerResult:
        if isinstance(action, BacktrackAction):
            return HandlerResult(True, "")

        if context.last_node.state is None:
            raise NotImplementedError()
            # Fallback to old logic

        state: PrimeState = context.last_node.state
        x = state.initial_number
        current_divider = state.current_product

        current_prod = x // current_divider

        if isinstance(action, DoneAction):
            new_divider = int(action.text)

            if current_prod % new_divider != 0:
                return HandlerResult(False, f"{current_prod} % {new_divider} != 0")

            return HandlerResult(
                (current_divider * new_divider) == x,
                f"({current_divider} * {new_divider}) != {x}",
            )

        if isinstance(action, NodeAction):
            new_divider = int(action.text)

            return HandlerResult(
                current_prod % new_divider == 0, f"{current_prod} % {new_divider} != 0"
            )

        return HandlerResult(False, "Unknown action")

    def __init__(self) -> None:
        super().__init__([self._basic_integer_handler, self._prime_logic_handler])
