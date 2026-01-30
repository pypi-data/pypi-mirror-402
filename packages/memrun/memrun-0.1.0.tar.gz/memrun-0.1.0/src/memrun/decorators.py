"""Decorators for memrun handlers."""

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class HandlerConfig:
    """Configuration for a handler."""

    sticky_key: str | None = None
    timeout_seconds: int = 300


def handler(
    sticky_key: str | None = None,
    timeout_seconds: int = 300,
) -> Callable[[F], F]:
    """Standalone decorator for marking a function as a handler.

    This is an alternative to using @svc.handler when you want to define
    the handler separately from the service.

    Args:
        sticky_key: Request field for sticky routing.
        timeout_seconds: Request timeout.

    Example:
        from memrun import handler

        @handler(sticky_key="user_id")
        def my_handler(ctx, req):
            return {"result": "ok"}
    """

    def decorator(fn: F) -> F:
        # Attach config to the function
        fn._memrun_handler_config = HandlerConfig(  # type: ignore
            sticky_key=sticky_key,
            timeout_seconds=timeout_seconds,
        )
        return fn

    return decorator


def get_handler_config(fn: Callable[..., Any]) -> HandlerConfig | None:
    """Get the handler config attached to a function."""
    return getattr(fn, "_memrun_handler_config", None)


@dataclass
class InitHandlerConfig:
    """Configuration for an initialization handler."""

    pass


def init_handler() -> Callable[[F], F]:
    """Decorator for marking a function as an initialization handler.

    The init handler is called once after the worker is initialized
    and before any request handlers are invoked. Use this to load
    models, embeddings, or other data into memory.

    Example:
        from memrun import init_handler, handler

        @init_handler()
        def setup(ctx):
            ctx.set_object("model", load_model())

        @handler()
        def predict(ctx, req):
            model = ctx.get_object("model")
            return {"prediction": model.predict(req["input"])}
    """

    def decorator(fn: F) -> F:
        fn._memrun_init_handler_config = InitHandlerConfig()  # type: ignore
        return fn

    return decorator


def get_init_handler_config(fn: Callable[..., Any]) -> InitHandlerConfig | None:
    """Get the init handler config attached to a function."""
    return getattr(fn, "_memrun_init_handler_config", None)
