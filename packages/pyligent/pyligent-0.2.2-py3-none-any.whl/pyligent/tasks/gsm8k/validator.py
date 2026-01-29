"""
Improved GSM8K validator.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import List, Optional, Set, Tuple

from pyligent.core import Validator
from pyligent.core.action import DoneAction, NodeAction
from pyligent.core.path import PathContext
from pyligent.core.validator import HandlerResult

# =========================
# Safe arithmetic evaluator
# =========================

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(node) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    # py<=3.7 compat
    if hasattr(ast, "Num") and isinstance(node, ast.Num):  # type: ignore[attr-defined]
        return node.n  # type: ignore[attr-defined]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    raise ValueError(f"Illegal expression node: {type(node).__name__}")


def normalize_expr_for_eval(s: str) -> str:
    # Normalize human math symbols to Python
    s = s.replace("×", "*").replace("·", "*")
    # Replace 'x' only when used between numbers (with or without spaces)
    s = re.sub(r"(?i)(?<=\d)\s*x\s*(?=\d)", "*", s)
    s = s.replace("÷", "/").replace("−", "-")
    # Strip currency/grouping on LHS if present
    s = s.replace("$", "")
    s = s.replace(",", "")
    return s


def safe_eval_expr(expr: str) -> float:
    """
    Evaluate a simple arithmetic expression safely:
    supports + - * / // % **, parentheses, and numerics.
    """
    expr = normalize_expr_for_eval(expr.strip())
    tree = ast.parse(expr, mode="eval")
    for n in ast.walk(tree):
        if isinstance(n, (ast.Call, ast.Name, getattr(ast, "Attribute", object))):
            raise ValueError("Functions, variables, or attributes are not allowed")
    val = _safe_eval(tree)
    return float(val)


def extract_numeric_literals_from_expr(expr: str) -> List[float]:
    expr = normalize_expr_for_eval(expr)
    tree = ast.parse(expr, mode="eval")
    nums: List[float] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            nums.append(float(n.value))
        elif hasattr(ast, "Num") and isinstance(n, ast.Num):  # type: ignore[attr-defined]
            nums.append(float(n.n))  # type: ignore[attr-defined]
    return nums


# =========================
# Parsing helpers & regexes
# =========================

# Robust numeric token (with optional $), stops before letters/hyphens; tolerates grouped commas and leading dot
NUM_TOKEN_RE = re.compile(
    r"""
    (?:
        \$?\s*           # optional dollar with optional space
        -?               # optional leading minus
        (?:
            (?:\d{1,3}(?:,\d{3})+)  # grouped integer like 1,234 or 22,500
            |
            \d+                       # plain integer
            |
            \.\d+                     # leading dot decimal like .5
        )
        (?:\.\d+)?      # optional decimal part after integer
    )
    """,
    re.VERBOSE,
)


def parse_numeric_str(s: str) -> float:
    """
    Extract the FIRST numeric token from s and parse it.

    Handles things like ' $22,500.00 ', '566-', '15. ', '$.75', etc.
    """
    m = NUM_TOKEN_RE.search(s)
    if not m:
        raise ValueError(f"No numeric token found in '{s}'")
    token = m.group(0)
    # strip $ and commas/spaces
    token = token.replace("$", "").replace(",", "").strip()
    # trim trailing period (common in prose)
    if token.endswith(".") and token.count(".") == 1:
        token = token[:-1]
    # trim dangling trailing hyphen (e.g., "566-")
    if token.endswith("-") and token.count("-") == 1:
        token = token[:-1]
    return float(token)


# Tag: << expr = inside >> printed
# Keep group 2/3 wide, then re-extract numeric via parse_numeric_str to survive junk/dangling '-'
CALC_TAG = re.compile(r"<<\s*([^<>]+?)\s*=\s*([^<>]+?)\s*>>\s*([^<>\n]+)")
FINAL_RE = re.compile(r"####\s*([^\n]+)")


def parse_answer_text(answer: str) -> Tuple[List[str], Optional[float]]:
    """
    Split an answer block into steps and final answer (if '#### N' present).
    Returns (steps_lines, final_value_or_None)
    """
    lines = [ln.strip() for ln in answer.strip().splitlines() if ln.strip()]
    final_val: Optional[float] = None
    final_idx: Optional[int] = None

    for i in range(len(lines) - 1, -1, -1):
        m = FINAL_RE.match(lines[i])
        if m:
            try:
                final_val = parse_numeric_str(m.group(1))
            except Exception:
                # Malformed #### value -> treat as absent
                final_val = None
            final_idx = i
            break

    steps = lines if final_idx is None else lines[:final_idx]
    return steps, final_val


def try_bare_equalities(
    step: str, eps: float = 1e-6
) -> Tuple[bool, List[float], List[str], Set[float]]:
    """
    Returns (math_ok, produced_vals, issues, used_numbers_set).

    Verifies numeric LHS subexpressions against numeric RHS numbers across '=' splits.
    Handles human 'x', '×', '÷', leading '.' decimals, and currency on RHS.
    Ignores segments with variables/letters on LHS (after normalization).
    """
    parts = [p.strip() for p in step.split("=")]
    if len(parts) < 2:
        return False, [], ["No '<<...>>' and no bare numeric equality found"], set()

    issues: List[str] = []
    produced: List[float] = []
    used_nums: Set[float] = set()
    ok_any = False

    for i in range(len(parts) - 1):
        lhs, rhs = parts[i].strip(), parts[i + 1].strip()
        lhs_norm = normalize_expr_for_eval(lhs)
        # Skip if letters remain after normalization (true variables)
        if re.search(r"[A-Za-z]", lhs_norm):
            continue
        try:
            lhs_val = safe_eval_expr(lhs_norm)
        except Exception:
            continue
        # Accept RHS with trailing units/words by extracting the first numeric token
        try:
            rhs_val = parse_numeric_str(rhs)
        except Exception:
            continue

        if abs(lhs_val - rhs_val) > eps:
            issues.append(
                f"Equality check failed: {lhs} != {rhs} ({lhs_val} vs {rhs_val})"
            )
            return False, [], issues, set()

        ok_any = True
        produced.append(rhs_val)
        for n in extract_numeric_literals_from_expr(lhs_norm):
            used_nums.add(n)

    if not ok_any:
        return False, [], ["No verifiable numeric sub-equality found"], set()
    return True, produced, issues, used_nums


# =========================
# Tolerant matching helpers
# =========================

CEIL_HINT_UNITS = (
    "bills",
    "packs",
    "boxes",
    "buses",
    "trips",
    "groups",
    "containers",
    "tables",
    "dozens",
    "cars",
    "bags",
    "bottles",
    "seats",
    "rooms",
    "tickets",
    "people",
    "students",
    "workers",
    "items",
    "bars",
    "bricks",
    "tiles",
)


def _rounding_reconcile(qtext: str, gold: float, got: float, eps: float) -> bool:
    """
    Try tolerant integer/rounding matching if plain compare fails.
    Includes rounding to nearest and ceil/floor in count-like contexts.
    """
    ql = qtext.lower()
    candidates = {got, round(got)}
    # Heuristic: if integer-ish contexts, also try ceil/floor
    if any(w in ql for w in CEIL_HINT_UNITS) or "how many" in ql:
        candidates.update({math.ceil(got), math.floor(got)})
    # Always allow tiny epsilon to integer
    for cand in candidates:
        if abs(gold - cand) <= eps:
            return True
    return False


def _cents_dollars_match(qtext: str, gold: float, got: float, eps: float) -> bool:
    """
    Heuristic reconciliation for cents vs dollars phrasing.
    """
    qlow = qtext.lower()
    # If the question is in cents (and not explicitly dollars), allow 100*x
    if ("cent" in qlow) and ("dollar" not in qlow):
        if abs(gold - 100.0 * got) <= eps:
            return True
    # If the question is in dollars (and not explicitly cents), allow x/100
    if ("dollar" in qlow) and ("cent" not in qlow):
        if abs(gold - got / 100.0) <= eps:
            return True
    # Be symmetric to be safe
    if ("cent" in qlow) and ("dollar" not in qlow):
        if abs(gold / 100.0 - got) <= eps:
            return True
    if ("dollar" in qlow) and ("cent" not in qlow):
        if abs(gold * 100.0 - got) <= eps:
            return True
    return False


# =========================
# Improved Validator
# =========================


class GSM8KValidator(Validator):
    """
    Improved GSM8K validator.

    Enhancements over the simple version:
    - NodeAction: If arithmetic tags (<< expr = inside >> printed) are present, verify them; if bare equalities with '=', verify numeric consistency; otherwise only structural check.
    - BacktrackAction: Same as baseline, checks target_id validity against context nodes.
    - DoneAction: Prefer '#### N' final extraction; numeric parsing tolerant to $, commas, trailing markers; supports rounding and cents↔dollars reconciliation when comparing to expected.
    """

    def _invalid_node_content_handler(
        self, action: NodeAction, context: PathContext
    ) -> HandlerResult:
        """
        Validate a NodeAction (reasoning step).

        Strategy:
        - If empty text -> invalid.
        - If contains calc tags, verify each tag: eval(expr) == inside == printed (with rounding tolerance for printed).
        - Else if contains '=', try bare equality checks on numeric subexpressions.
        - Else accept as structurally valid (lightweight).
        """

        text = action.text.strip()
        question = context.nodes[0].action.text if context.nodes else ""

        # Verify calc tags if present
        tags = list(CALC_TAG.finditer(text))
        if tags:
            for m in tags:
                expr = m.group(1).strip()
                try:
                    val_inside = parse_numeric_str(m.group(2))
                except Exception:
                    return HandlerResult(False, " val_inside = parse_numeric_str fails")
                try:
                    val_printed = parse_numeric_str(m.group(3))
                except Exception:
                    return HandlerResult(False, "val_printed = parse_numeric_str fails")
                try:
                    eval_val = safe_eval_expr(expr)
                except Exception:
                    return HandlerResult(False, "safe_eval_expr fails")

                # eval(expr) must match inside
                if abs(eval_val - val_inside) > self.eps:
                    return HandlerResult(False, "eval(expr) does not match inside")

                # inside must match printed with rounding reconciliation allowed
                if (abs(val_inside - val_printed) > self.eps) and (
                    not _rounding_reconcile(question, val_printed, val_inside, self.eps)
                ):
                    return HandlerResult(False, "_rounding_reconcile fails")

            # All tags validated
            return HandlerResult(True)

        # If no tags, try bare equality checks if '=' appears
        if "=" in text:
            if self.enable_bare_equalities:
                be_ok, _, _, _ = try_bare_equalities(text, self.eps)
                return HandlerResult(be_ok, "try_bare_equalities fails")
            return HandlerResult(True)

        # Otherwise, accept as structurally valid step
        return HandlerResult(True)

    def _validate_done_action(
        self, action: DoneAction, context: PathContext
    ) -> HandlerResult:
        """
        Validate a DoneAction (final answer).

        Behavior:
        - If no expected answers provided, accept all done actions.
        - Otherwise, find the question (root node text) and expected answer string.
        - Extract predicted final, preferring '#### N' if present; fallback to first numeric token.
        - Compare with tolerance; allow cents↔dollars reconciliation and rounding tolerance in count-like contexts.
        - If numeric extraction fails for either side, fallback to strict string equality (trimmed).
        """
        # If no expected answers provided, accept all done actions
        if not self.expected_answers:  # ? Check
            return HandlerResult(True)

        question = context.nodes[0].action.text
        if question not in self.expected_answers:
            # No expected answer, accept it
            return HandlerResult(True)

        expected_answer = self.expected_answers[question]

        # Prefer '#### N' extraction from the produced answer; fallback to numeric token
        _steps_text, final_in_text = parse_answer_text(action.answer)
        try:
            predicted_numeric = (
                final_in_text
                if final_in_text is not None
                else parse_numeric_str(action.answer)
            )
        except Exception:
            predicted_numeric = None

        try:
            expected_numeric = parse_numeric_str(expected_answer)
        except Exception:
            expected_numeric = None

        # Compare answers
        if predicted_numeric is not None and expected_numeric is not None:
            if abs(predicted_numeric - expected_numeric) <= self.eps:
                return HandlerResult(True)
            # Unit-aware fallback (cents vs dollars)
            if _cents_dollars_match(
                question, expected_numeric, predicted_numeric, self.eps
            ):
                return HandlerResult(True)
            # Rounding tolerance (nearest / ceil/floor contexts)
            if _rounding_reconcile(
                question, expected_numeric, predicted_numeric, self.eps
            ):
                return HandlerResult(True)
            return HandlerResult(
                False, f"Predicted {predicted_numeric} != expected {expected_numeric}"
            )

        # Could not extract numeric answer reliably; fall back to string comparison
        return HandlerResult(
            action.answer.strip() == expected_answer.strip(),
            f"String comparison fails ({action.answer.strip()} != {expected_answer.strip()})",
        )

    def __init__(
        self,
        expected_answers: Optional[dict[str, str]] = None,
        eps: float = 1e-6,
        enable_bare_equalities: bool = False,
    ):
        """
        Initialize GSM8K validator.

        Args:
            expected_answers: Dictionary mapping question text to expected answer strings.
                                If None, DoneActions are always considered valid.
            eps: Numeric tolerance for comparisons.
            enable_bare_equalities: Whether to run lightweight '=' arithmetic validation.
        """
        super().__init__([self._invalid_node_content_handler, self._validate_done_action])
        self.expected_answers = expected_answers or {}
        self.eps = eps
        self.enable_bare_equalities = enable_bare_equalities
