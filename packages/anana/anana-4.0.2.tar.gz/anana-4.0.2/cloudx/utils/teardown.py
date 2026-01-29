import inspect
from typing import Any, Callable, Iterable, List, Optional, Tuple, TYPE_CHECKING

from .container import Container
from .logger import logger
from ..middlewares.aws_lambda_extensions import (
    _signal_handler_complete,
    is_async_processor_active,
    start_async_task,
)

if TYPE_CHECKING:
    from ..asgi import LocalRequest, Request
    from ..asgi import Response
else:
    # Avoid circular import at runtime
    LocalRequest = Any
    Request = Any
    Response = Any

def teardown(func: Optional[Callable[[LocalRequest, Response], None]] = None) -> Callable[[LocalRequest, Response], None]:
    """Decorator used to register teardown callbacks executed during shutdown.
    
    Teardown functions must accept exactly two positional parameters:
    - request: Request (or LocalRequest) - The request object
    - response: Response - The response object
    
    Examples:
        from cloudx.utils import teardown, Request
        from cloudx import Response
        
        @teardown
        def my_teardown(request: Request, response: Response):
            # Process teardown logic
            pass
    """

    def _register(target: Callable[[LocalRequest, Response], None]) -> Callable[[LocalRequest, Response], None]:
        sig = inspect.signature(target)
        params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        if len(params) != 2:
            raise TypeError("teardown function must accept exactly two positional parameters: request (LocalRequest) and response (Response)")
        Container()._register_teardown(target)
        return target

    if func is None:
        return _register
    return _register(func)


def _execute_teardowns(handlers: Iterable[Callable[[LocalRequest, Response], None]], request: LocalRequest, response: Response) -> None:
    for handler in handlers:
        try:
            handler(request, response)
        except Exception as exc:  # pragma: no cover
            name = getattr(handler, "__name__", repr(handler))
            logger.error(f"Teardown '{name}' failed: {exc}")


def schedule_teardowns(
    handlers: List[Callable[[LocalRequest, Response], None]],
    request: LocalRequest,
    response: Response,
    request_id: Optional[str],
) -> None:
    """Run teardown callbacks inline or through the Lambda sidecar.
    
    Parameters:
        handlers: List of teardown handler functions
        request: The request object
        response: The response object
        request_id: Optional request ID for async processing
    """
    # Always signal handler completion, even if no teardowns
    # This allows the extension to check and exit quickly if no teardowns exist
    if request_id:
        from ..middlewares.aws_lambda_extensions import _signal_handler_complete
        _signal_handler_complete(request_id)

    if not handlers:
        return

    if request_id and is_async_processor_active():

        def _async_task(data: Tuple[LocalRequest, Response]) -> None:
            req, resp = data
            _execute_teardowns(handlers, req, resp)

        start_async_task(_async_task, (request, response), request_id=request_id)
    else:
        _execute_teardowns(handlers, request, response)
