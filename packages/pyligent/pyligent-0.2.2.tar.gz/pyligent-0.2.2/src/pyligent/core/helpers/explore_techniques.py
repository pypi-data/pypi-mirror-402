from typing import Callable, Literal

ExploreTechniques = Literal["exponential", "linear"]
MaxActionsFunction = Callable[[int, int, int], int]


def _max_actions_function_exp(_t: int, _depth: int, B: int) -> int:
    """Exponential: return B at all depths."""
    return B


def _max_actions_function_linear(_t: int, depth: int, B: int) -> int:
    """Linear: B at depth 0, then 1 for deeper nodes."""
    return B if depth == 0 else 1


MAX_ACTIONS_DICT: dict[ExploreTechniques, MaxActionsFunction] = {
    "exponential": _max_actions_function_exp,
    "linear": _max_actions_function_linear,
}
