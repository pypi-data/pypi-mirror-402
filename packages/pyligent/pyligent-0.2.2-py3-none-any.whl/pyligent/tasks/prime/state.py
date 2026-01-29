from dataclasses import dataclass, field
from typing import Optional

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.state import StateEngine


@dataclass
class PrimeState:
    initial_number: int
    dividers: list[int] = field(default_factory=list)
    current_product: int = 1

    def add_divider(self, divider: int) -> "PrimeState":
        return PrimeState(
            initial_number=self.initial_number,
            dividers=self.dividers + [divider],
            current_product=self.current_product * divider,
        )

    def __str__(self) -> str:
        return (
            f"TARGET = {self.initial_number}\n"
            + " * ".join(
                map(str, self.dividers if len(self.dividers) > 1 else [1] + self.dividers)
            )
            + f" = {self.current_product}"
        )


class PrimeStateEngine(StateEngine):
    def reduce(self, parent_state: Optional[PrimeState], action: Action) -> PrimeState:
        if parent_state is None:
            raise NotImplementedError()

        try:
            if isinstance(action, NodeAction):
                new_divider = int(action.text)
                return parent_state.add_divider(new_divider)

            if isinstance(action, DoneAction):
                # return (prev_text + "\n[ANSWER] " + action.answer).strip()
                new_divider = int(action.answer)
                return parent_state.add_divider(new_divider)

            if isinstance(action, BacktrackAction):
                # Backtrack doesn't modify state
                return parent_state
        except:
            # Assume Validator catch all the errors
            pass

        return parent_state
