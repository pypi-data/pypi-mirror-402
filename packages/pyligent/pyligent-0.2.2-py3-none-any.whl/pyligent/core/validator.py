from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional, get_type_hints

from loguru import logger

from pyligent.core.action import Action, BacktrackAction, DoneAction, NodeAction
from pyligent.core.path import PathContext


@dataclass
class HandlerResult:
    valid: bool
    comment: str = ""


ValidatorResult = Optional[HandlerResult]


ContextHandler = Callable[[PathContext], HandlerResult]
ActionHandler = Callable[[Action, PathContext], HandlerResult]
NodeActionHandler = Callable[[NodeAction, PathContext], HandlerResult]
BacktrackActionHandler = Callable[[BacktrackAction, PathContext], HandlerResult]
DoneActionHandler = Callable[[DoneAction, PathContext], HandlerResult]
ValidatorHandler = (
    ContextHandler
    | ActionHandler
    | NodeActionHandler
    | BacktrackActionHandler
    | DoneActionHandler
)


class ValidationScope(Enum):
    """Categorizes validator handlers by scope"""

    CONTEXT = auto()
    ACTION_GENERIC = auto()
    NODE_ACTION = auto()
    BACKTRACK_ACTION = auto()
    DONE_ACTION = auto()


class Validator[T]:
    """Validates actions in context with pluggable handler system"""

    def __init__(self, handlers: Optional[list[ValidatorHandler]] = None):
        self._handlers: dict[ValidationScope, list[Callable]] = {
            scope: [] for scope in ValidationScope
        }

        # Register default handlers
        self._register_default_handlers()

        # Register custom handlers
        if handlers:
            for handler in handlers:
                self.register_handler(handler)

    def register_handler(self, handler: ValidatorHandler):
        """Register a validation handler based on its signature"""
        scope = self._infer_scope(handler)
        self._handlers[scope].append(handler)

    def _infer_scope(self, handler: ValidatorHandler) -> ValidationScope:
        """Infer validation scope from handler signature"""
        hints = get_type_hints(handler)
        param_types = list(hints.values())

        if not param_types:
            raise ValueError(f"Handler {handler} has no typed parameters")

        first_param_type = param_types[0]

        # Map parameter type to scope
        scope_mapping = {
            PathContext: ValidationScope.CONTEXT,
            Action: ValidationScope.ACTION_GENERIC,
            NodeAction: ValidationScope.NODE_ACTION,
            BacktrackAction: ValidationScope.BACKTRACK_ACTION,
            DoneAction: ValidationScope.DONE_ACTION,
        }

        for param_type, scope in scope_mapping.items():
            if first_param_type == param_type or first_param_type is param_type:
                return scope

        raise ValueError(f"Unknown parameter type {first_param_type} for handler")

    def validate(self, action: Action, context: PathContext[T]) -> ValidatorResult:
        """Run validation chain and return first failure or None"""

        # Validate context
        if result := self._run_handlers(ValidationScope.CONTEXT, context):
            return result

        # Validate action (generic)
        if result := self._run_handlers(ValidationScope.ACTION_GENERIC, action, context):
            return result

        # Validate specific action type
        type_scope_map = {
            NodeAction: ValidationScope.NODE_ACTION,
            BacktrackAction: ValidationScope.BACKTRACK_ACTION,
            DoneAction: ValidationScope.DONE_ACTION,
        }

        for action_type, scope in type_scope_map.items():
            if isinstance(action, action_type):
                return self._run_handlers(scope, action, context)

        logger.warning(f"Unknown action type: {type(action)}")
        return None

    def _run_handlers(self, scope: ValidationScope, *args) -> ValidatorResult:
        """Execute all handlers for a scope"""
        try:
            for handler in self._handlers[scope]:
                result = handler(*args)
                if result is not None and not result.valid:
                    return result
        except BaseException as e:
            return HandlerResult(False, str(e))
        return None

    def _register_default_handlers(self):
        """Register built-in validation rules"""
        default_handlers = [
            self._empty_path_context_handler,
            self._empty_done_handler,
            self._backtrack_to_previous_handler,
            self._empty_node_handler,
            self._sequential_id_handler,
        ]
        for handler in default_handlers:
            self.register_handler(handler)

    @staticmethod
    def _sequential_id_handler(action: NodeAction, context: PathContext) -> HandlerResult:
        # Find the last committed NodeAction id from the context
        last_id = -1
        for node in reversed(context.nodes):
            if isinstance(node.action, NodeAction):
                last_id = node.action.node_id
                break

        # If there was no prior NodeAction, the first expected id is 0
        expected = last_id + 1

        return HandlerResult(
            action.node_id == expected,
            comment=f"Node id should be {expected}, received {action.node_id}",
        )

    @staticmethod
    def _empty_node_handler(action: NodeAction, _context: PathContext) -> HandlerResult:
        return HandlerResult(len(action.text.strip()) > 0, comment="Content is empty")

    @staticmethod
    def _backtrack_to_previous_handler(
        action: BacktrackAction, context: PathContext
    ) -> HandlerResult:
        valid_ids = {
            node.action.node_id
            for node in context.nodes[:-1]
            if isinstance(node.action, NodeAction)
        }  # Can not backtrack to last NodeAction
        return HandlerResult(
            action.target_id in valid_ids,
            f"No id={action.target_id} among previous nodes",
        )

    @staticmethod
    def _empty_done_handler(action: DoneAction, _context: PathContext) -> HandlerResult:
        return HandlerResult(len(action.text.strip()) > 0, comment="Content is empty")

    @staticmethod
    def _empty_path_context_handler(context: PathContext) -> HandlerResult:
        return HandlerResult(len(context.nodes) != 0, comment="Path is empty")
