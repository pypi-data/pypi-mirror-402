from .inject import inject, bind
from .bootstrap import bootstrap, mock_env
from .teardown import teardown
from .asyncify import asyncify
from .serializator import BaseModel

# Lazy import to avoid circular dependencies
def __getattr__(name):
    if name == "Request":
        from ..asgi import LocalRequest as Request
        return Request
    raise AttributeError(f"module 'cloudx.utils' has no attribute '{name}'")

__all__ = ["inject", "bootstrap", "bind", "mock_env", "asyncify", "BaseModel", "teardown", "Request"]
