"""Handler extractor for parsing Python files and extracting @svc.handler metadata."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class HandlerInfo:
    """Information about a discovered handler."""

    def __init__(
        self,
        function_name: str,
        sticky_key: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.function_name = function_name
        self.sticky_key = sticky_key
        self.timeout_seconds = timeout_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for manifest."""
        return {
            "function_name": self.function_name,
            "sticky_key": self.sticky_key,
            "timeout_seconds": self.timeout_seconds,
        }


class InitHandlerInfo:
    """Information about a discovered initialization handler."""

    def __init__(self, function_name: str):
        self.function_name = function_name

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for manifest."""
        return {
            "function": self.function_name,
        }


class HandlerExtractor(ast.NodeVisitor):
    """AST visitor to find @svc.handler, @handler, @svc.init_handler, and @init_handler decorated functions."""

    def __init__(self):
        self.handlers: list[HandlerInfo] = []
        self.init_handlers: list[InitHandlerInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions and check for handler decorators."""
        for decorator in node.decorator_list:
            handler_info = self._parse_handler_decorator(decorator, node.name)
            if handler_info:
                self.handlers.append(handler_info)
            init_handler_info = self._parse_init_handler_decorator(decorator, node.name)
            if init_handler_info:
                self.init_handlers.append(init_handler_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions and check for handler decorators."""
        for decorator in node.decorator_list:
            handler_info = self._parse_handler_decorator(decorator, node.name)
            if handler_info:
                self.handlers.append(handler_info)
            init_handler_info = self._parse_init_handler_decorator(decorator, node.name)
            if init_handler_info:
                self.init_handlers.append(init_handler_info)
        self.generic_visit(node)

    def _parse_handler_decorator(
        self, decorator: ast.expr, func_name: str
    ) -> HandlerInfo | None:
        """Parse a decorator and return HandlerInfo if it's a handler decorator."""
        # Check for @svc.handler(...) or @handler(...)
        if isinstance(decorator, ast.Call):
            if self._is_handler_call(decorator):
                kwargs = self._extract_decorator_kwargs(decorator)
                return HandlerInfo(
                    function_name=func_name,
                    sticky_key=kwargs.get("sticky_key"),
                    timeout_seconds=kwargs.get("timeout_seconds"),
                )
        # Check for @svc.handler or @handler (without parentheses)
        elif isinstance(decorator, ast.Attribute):
            if decorator.attr == "handler":
                return HandlerInfo(function_name=func_name)
        elif isinstance(decorator, ast.Name):
            if decorator.id == "handler":
                return HandlerInfo(function_name=func_name)

        return None

    def _is_handler_call(self, call: ast.Call) -> bool:
        """Check if a Call node is a handler decorator call."""
        func = call.func
        # @svc.handler(...)
        if isinstance(func, ast.Attribute) and func.attr == "handler":
            return True
        # @handler(...)
        if isinstance(func, ast.Name) and func.id == "handler":
            return True
        return False

    def _parse_init_handler_decorator(
        self, decorator: ast.expr, func_name: str
    ) -> InitHandlerInfo | None:
        """Parse a decorator and return InitHandlerInfo if it's an init_handler decorator."""
        # Check for @svc.init_handler(...) or @init_handler(...)
        if isinstance(decorator, ast.Call):
            if self._is_init_handler_call(decorator):
                return InitHandlerInfo(function_name=func_name)
        # Check for @svc.init_handler or @init_handler (without parentheses)
        elif isinstance(decorator, ast.Attribute):
            if decorator.attr == "init_handler":
                return InitHandlerInfo(function_name=func_name)
        elif isinstance(decorator, ast.Name):
            if decorator.id == "init_handler":
                return InitHandlerInfo(function_name=func_name)

        return None

    def _is_init_handler_call(self, call: ast.Call) -> bool:
        """Check if a Call node is an init_handler decorator call."""
        func = call.func
        # @svc.init_handler(...)
        if isinstance(func, ast.Attribute) and func.attr == "init_handler":
            return True
        # @init_handler(...)
        if isinstance(func, ast.Name) and func.id == "init_handler":
            return True
        return False

    def _extract_decorator_kwargs(self, call: ast.Call) -> dict[str, Any]:
        """Extract keyword arguments from a decorator call."""
        kwargs: dict[str, Any] = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                continue
            value = self._eval_constant(keyword.value)
            if value is not None:
                kwargs[keyword.arg] = value
        return kwargs

    def _eval_constant(self, node: ast.expr) -> Any:
        """Safely evaluate a constant node."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        if isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        if isinstance(node, ast.NameConstant):  # Python 3.7 compatibility
            return node.value
        return None


@dataclass
class HandlerFileInfo:
    """Combined information about handlers found in a file."""

    handler: HandlerInfo
    init_handler: InitHandlerInfo | None = None


def validate_handler_file(file_path: Path) -> HandlerFileInfo:
    """Parse a Python file and validate it has exactly one @svc.handler decorator.

    Args:
        file_path: Path to the Python file.

    Returns:
        HandlerFileInfo with handler and optional init_handler metadata.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file doesn't contain exactly one handler.
        SyntaxError: If the file has invalid Python syntax.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Handler file not found: {file_path}")

    if not file_path.suffix == ".py":
        raise ValueError(f"Handler file must be a Python file (.py): {file_path}")

    source = file_path.read_text()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax in {file_path}: {e}")

    extractor = HandlerExtractor()
    extractor.visit(tree)

    if len(extractor.handlers) == 0:
        raise ValueError(
            f"No @svc.handler or @handler decorated function found in {file_path}. "
            "Ensure your handler is decorated with @svc.handler(...) or @handler(...)."
        )

    if len(extractor.handlers) > 1:
        names = [h.function_name for h in extractor.handlers]
        raise ValueError(
            f"Found {len(extractor.handlers)} handlers in {file_path}: {names}. "
            "Each handler file must contain exactly one @svc.handler decorated function."
        )

    if len(extractor.init_handlers) > 1:
        names = [h.function_name for h in extractor.init_handlers]
        raise ValueError(
            f"Found {len(extractor.init_handlers)} init handlers in {file_path}: {names}. "
            "Each handler file must contain at most one @svc.init_handler decorated function."
        )

    init_handler = extractor.init_handlers[0] if extractor.init_handlers else None

    return HandlerFileInfo(
        handler=extractor.handlers[0],
        init_handler=init_handler,
    )
