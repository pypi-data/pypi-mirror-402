from typing import Callable, List, Union, Dict, Any, Optional

from .asgi import ASGICore
from .common import SingletonMeta
from .middlewares.aws_lambda import AWSMiddleware
from .middlewares.aws_lambda_extensions import start_async_processor
from .utils.teardown import schedule_teardowns
from .utils.container import Container
from .asgi import request
from .asgi import Response

class CloudX(metaclass=SingletonMeta):
    """
    Middleware to handle CloudEvents, manage health checks, and integrate with ASGI applications.
    """

    aws: Optional[AWSMiddleware]
    """
    AWS middleware accessor used to register AWS event handlers and to handle
    AWS Lambda events. It may be None if AWS middleware is not configured.
    """

    def __init__(self, core: ASGICore, middlewares: Dict[str, Any]) -> None:
        """
        Initialize KnativeMiddleware.

        Parameters:
            app (ASGIApp): The core ASGI application.
            middleware (Callable): Middleware to handle cloud-compatible events.
        """
        self.app = core
        self.middlewares = middlewares

        # Create a property for each middleware
        for key, middleware in middlewares.items():
            setattr(self, key, middleware)

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> Any:
        """
        Handle an incoming ASGI request.

        Parameters:
            scope (Union[Dict[str, Any], bytes]): The ASGI scope dictionary or binary data.
            receive (Callable): The receive function to get messages.
            send (Callable): The send function to send messages.        
        Returns:
            The response from the handler.
        """
        return await self.app(scope, receive, send)
    
    def aws_lambda_handler(self, event: Dict[str, Any], context: Any) -> Any:
        """
        AWS Lambda entry point. Adapts AWS events into ASGI requests using the AWS middleware.

        Parameters:
            - `event` (Dict[str, Any]): The raw AWS event.
            - `context` (Any): The Lambda context object.

        Returns:
            Dict[str, Any]: The AWS-compatible response returned by the selected middleware.

        Notes:
            - For API Gateway/Function URL events, this returns an HTTP-style response.
            - For SQS/S3/DynamoDB/etc., batch semantics apply as documented in the AWS middleware.
        """
        container = Container()
        teardowns = list(container.teardowns)

        # Strategy 2: Try registration from handler if INIT phase registration failed
        # This provides a second chance for registration (e.g., if runtime API wasn't ready during INIT)
        # If this also fails, start_async_processor() will gracefully fall back to inline execution
        if teardowns:
            start_async_processor()

        response = self.middlewares["aws"](event=event, context=context)

        if teardowns:
            request_id = getattr(context, "aws_request_id", None)
            # Get the current request from context if available
            try:
                current_request = request._current_request.get(None)
                if current_request is None:
                    # If no request in context, create a minimal one for teardown
                    from .asgi import LocalRequest
                    current_request = LocalRequest(
                        method="POST",
                        path="/",
                        headers={},
                        body=b"",
                        query_string=b"",
                        scheme="https",
                        server=("0.0.0.0", 443),
                        path_params={},
                        metadata={"context": context}
                    )
                # Convert response dict to Response object if needed
                if isinstance(response, dict):
                    response_obj = Response(
                        content=response.get("body", ""),
                        status_code=response.get("statusCode", 200),
                        headers=response.get("headers", {})
                    )
                else:
                    response_obj = response
                schedule_teardowns(teardowns, current_request, response_obj, request_id)
            except Exception as ex:
                # Fallback if request context is not available
                from .asgi import LocalRequest
                from .asgi import Response
                fallback_request = LocalRequest(
                    method="POST",
                    path="/",
                    headers={},
                    body=b"",
                    query_string=b"",
                    scheme="https",
                    server=("0.0.0.0", 443),
                    path_params={},
                    metadata={"context": context}
                )
                if isinstance(response, dict):
                    fallback_response = Response(
                        content=response.get("body", ""),
                        status_code=response.get("statusCode", 200),
                        headers=response.get("headers", {})
                    )
                else:
                    fallback_response = response
                schedule_teardowns(teardowns, fallback_request, fallback_response, request_id)

        return response

    def route(self, 
              path: str, 
              methods: Union[str, List[str]] = None, 
              **extra: Any) -> Callable:
        """
        Register a route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports path params with `{param}` placeholders, e.g. `/items/{item_id}`.
            - `methods` (Union[str, List[str]]): Allowed HTTP methods (e.g., "GET", "POST").
            - `extra`: Additional metadata attached to the route. The `trigger` key, if provided, is exposed as `request.source`.

        Returns:
            Callable: The registered callback function.

        Payload (HTTP requests):
            - `request.method`: HTTP method.
            - `request.path`: Matched path; `request.path_params` contains parsed `{}` placeholders.
            - `request.query_params`: Parsed query parameters dict.
            - `request.headers`: Incoming headers (case preserved on access).
            - `request.json` / `request.text` / `request.form` / `request.body`: Body helpers (JSON, text, form, raw bytes).
            - `request.url`, `request.content_length`, `request.content_type`.
        """
        
        return self.app.route(path, methods, extra)

    def get(self, path: str, **extra: Any) -> Callable:
        """
        Register a GET route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP GET): See `route`.
        """
        return self.app.route(path, "GET", extra)

    def post(self, path: str, **extra: Any) -> Callable:
        """
        Register a POST route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP POST): See `route`.
        """
        return self.app.route(path, "POST", extra)

    def put(self, path: str, **extra: Any) -> Callable:
        """
        Register a PUT route in the core ASG I app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP PUT): See `route`.
        """
        return self.app.route(path, "PUT", extra)

    def delete(self, path: str, **extra: Any) -> Callable:
        """
        Register a DELETE route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP DELETE): See `route`.
        """
        return self.app.route(path, "DELETE", extra)

    def patch(self, path: str, **extra: Any) -> Callable:
        """
        Register a PATCH route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP PATCH): See `route`.
        """
        return self.app.route(path, "PATCH", extra)

    def options(self, path: str, **extra: Any) -> Callable:
        """
        Register an OPTIONS route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP OPTIONS): See `route`.
        """
        return self.app.route(path, "OPTIONS", extra)

    def head(self, path: str, **extra: Any) -> Callable:
        """
        Register a HEAD route in the core ASGI app.

        Parameters:
            - `path` (str): Route path. Supports `{param}` placeholders.
            - `extra`: Additional metadata attached to the route.

        Payload (HTTP HEAD): See `route`. The response body is stripped.
        """
        return self.app.route(path, "HEAD", extra)    

    def boot(self, directory: Union[str, List[str]] = None) -> None:
        """
        Forward the boot call to the underlying ASGI application.

        Parameters:
            directory (Union[str, List[str]]): Directory or list of directories containing service definitions.

        Raises:
            Exception: Propagates exceptions from the ASGI application"s boot method.
        """
        self.app.boot(directory)

    def reboot(self, directory: str) -> None:
        """
        Reboot the core ASGI application by reloading routes.

        Parameters:
            directory (str): Directory containing route definitions.
        """
        self.app.reboot(directory)
