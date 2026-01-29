from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

from .asgi import request, Request, LocalRequest
from .asgi import Response


class _CloudXProxy:
    """Lazily instantiate the CloudX singleton to keep import overhead minimal."""

    __slots__ = ("_instance",)

    def __init__(self) -> None:
        object.__setattr__(self, "_instance", None)

    def _ensure_instance(self):
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            from .asgi import ASGICore
            from .middlewares.aws_lambda import AWSMiddleware
            from .cloudx import CloudX

            core = ASGICore()
            middlewares_registry = {"aws": AWSMiddleware(core)}
            instance = CloudX(core, middlewares_registry)
            object.__setattr__(self, "_instance", instance)
        return instance

    def __getattr__(self, item):
        return getattr(self._ensure_instance(), item)

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        instance = self._ensure_instance()
        return await instance(scope, receive, send)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._ensure_instance(), name, value)

    def __delattr__(self, name):
        if name in self.__slots__:
            object.__delattr__(self, name)
        else:
            delattr(self._ensure_instance(), name)


x = _CloudXProxy()

_LAZY_ATTRS = {
    "ASGICore": ("cloudx.asgi", "ASGICore"),
    "AWSMiddleware": ("cloudx.middlewares.aws_lambda", "AWSMiddleware"),
    "CloudX": ("cloudx.cloudx", "CloudX"),
}


def __getattr__(name):
    if name in _LAZY_ATTRS:
        module_name, attr_name = _LAZY_ATTRS[name]
        module = __import__(module_name, fromlist=[attr_name])
        value = getattr(module, attr_name)
        globals()[name] = value  # Cache for subsequent lookups
        return value
    raise AttributeError(f"module 'cloudx' has no attribute '{name}'")


def __dir__():
    return sorted(set(globals().keys()) | set(_LAZY_ATTRS.keys()))


if TYPE_CHECKING:  # pragma: no cover - helpers for static type checkers
    from .asgi import ASGICore
    from .middlewares.aws_lambda import AWSMiddleware
    from .cloudx import CloudX

    x: "CloudX"

__all__ = [
    "x",
    "request",
    "Response",
    "Request",
]
