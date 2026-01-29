import contextvars
import json
import random
import string
import logging
from ..utils.logger import logger
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple, List, Union, Callable
from ..common import SingletonMeta
from ..methods import Method

class LocalRequest:
    """
    Represents an HTTP request processed by the ASGI server.
    """
    def __init__(self, 
                 method: str, 
                 path: str, 
                 headers: Dict[str, str], 
                 body: bytes, 
                 query_string: bytes, 
                 scheme: str, 
                 server: Tuple[str, int], 
                 path_params: Dict[str, str], 
                 metadata: Dict[str, Any] = {}) -> None:
        # Internal request container constructed by the ASGI core/middlewares.
        self._method = method
        self._path = path
        self._headers = headers.copy()
        self._body = body if body is not None else b""
        self._query_string = query_string
        self._path_params = path_params
        self._scheme = scheme
        self._server = server
        self._metadata = metadata
        context = metadata.get("context", None)
        if hasattr(context, "aws_request_id"):
            self._request_id = context.aws_request_id
        else:
            self._request_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    @property
    def method(self) -> str:
        """Returns the normalized request method."""
        return Method[self._method]

    @property
    def path(self) -> str:
        """Returns the request path."""
        return self._path

    @property
    def full_path(self) -> str:
        """Returns the full path including query parameters."""
        from urllib.parse import urlencode
        query_string = urlencode(self.query_params)
        if query_string:
            return f"{self._path}?{query_string}"
        return self._path

    @property
    def headers(self) -> Dict[str, str]:
        """Returns the request headers (keys normalized to lowercase)."""
        return self._headers.copy()

    @property
    def body(self) -> bytes:
        """Returns the raw request body as bytes (may be binary)."""
        if self._body is None:
            return None
        else:
            return self._body

    @property
    def form(self) -> Optional[Dict[str, Union[str, List[str]]]]:
        """
        Parses and returns URL-encoded form data from the body.

        Returns:
            Optional[Dict[str, Union[str, List[str]]]]: The parsed form data or None.
        """
        try:
            from urllib.parse import parse_qs
            form = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(self.body.decode()).items()}
            return None if form == {} else form
        except Exception:
            return None

    @property
    def text(self) -> Optional[str]:
        """
        Returns the request body as a UTF-8 string when it appears to be text.

        Returns:
            Optional[str]: The body as a string, or None for binary/empty.
        """
        try:
            if any(b for b in self.body[:8] if b < 9 or b > 127):  # Sample first few bytes
                return None
            
            decoded = str(self.json) if self.json is not None else self.body.decode("utf-8")
            return None if decoded == "" else decoded
        except Exception:
            return None

    @property
    def query_params(self) -> Dict[str, Any]:
        """
        Parses and returns query parameters from the query string.

        Returns:
            Dict[str, Any]: The parsed query parameters.
        """
        
        from urllib.parse import parse_qs
        raw_params = parse_qs(self._query_string.decode(), keep_blank_values=True)
        normalized_params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in raw_params.items()}
        return normalized_params

    @property
    def path_params(self) -> Dict[str, str]:
        """
        Returns the parsed path parameters captured from placeholders in the route.
        """
        return self._path_params

    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """
        Parses and returns JSON data from the body.

        Returns:
            Optional[Dict[str, Any]]: The parsed JSON data.
        """
        import json
        try:
            return json.loads(self.body)
        except Exception as ex:
            return None

    @property
    def url(self) -> str:
        """
        Constructs and returns the full URL including the query string.

        Returns:
            str: The full URL.
        """
        from urllib.parse import urlencode, urlunparse
        netloc = f"{self._server[0]}:{self._server[1]}"
        query_string = urlencode(self.query_params, doseq=True)
        return urlunparse((self._scheme, netloc, self._path, "", query_string, ""))

    @property
    def content_length(self) -> int:
        """
        Returns the Content-Length of the request as an integer.
        """
        try:
            # Case-insensitive header lookup
            for header_key in self.headers:
                if header_key.lower() == "content-length":
                    content_length = self.headers[header_key].strip()
                    length = int(content_length)
                    return max(0, length)  # Ensure non-negative
            return 0
        except (ValueError, TypeError):
            return 0

    @property
    def content_type(self) -> str:
        """
        Returns the Content-Type header value, or an empty string if missing.
        """
        for header_key in self.headers:
            if header_key.lower() == "content-type":
                return self.headers[header_key]
        return ""

    @property
    def request_id(self) -> str:
        """Gets or sets the unique request ID (AWS context id or generated)."""
        return self._request_id
    @request_id.setter
    def request_id(self, value: str) -> None:
        self._request_id = value

    @property
    def metadata(self) -> Dict[str, Any]:
        """Returns the metadata associated with the request."""
        return self._metadata

    @staticmethod
    async def from_scope(scope: Dict[str, Any], 
                         receive: Callable[[], Any], 
                         path_params: Dict[str, str] = None) -> "LocalRequest":
        """Builds the internal request object from an ASGI scope (internal)."""
        method = scope["method"]
        path = scope["path"]
        headers = {k.decode(): v.decode() for k, v in scope["headers"]}
        body = b""
        query_string = scope["query_string"]
        scheme = scope["scheme"]
        server = scope["server"]
        metadata = scope.get("metadata", {})
        trigger = scope["extra"].get("trigger", None)
        if trigger is not None:
            metadata["source"] = trigger
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body_part = message.get("body", b"")
                if isinstance(body_part, (dict, list)):
                    body_part = json.dumps(body_part, default=lambda o: float(o) if isinstance(o, Decimal) else o, indent=2).encode()
                elif isinstance(body_part, (int, float, bool, Decimal)):
                    body_part = str(body_part).encode()
                elif body_part is None:
                    body_part = b""
                body += body_part
                if not message.get("more_body", False):
                    break
        return LocalRequest(method, path, headers, body, query_string, scheme, server, path_params or {}, metadata)


class Request(metaclass=SingletonMeta):
    """
    Public request proxy used in controllers.

    Represents both traditional HTTP requests (API Gateway/Function URL/ASGI)
    and event-driven invocations adapted into HTTP-like requests (SQS, S3, DynamoDB, etc.).

    Common fields:
    - method/path/path_params/query_params/headers
    - body/json/text/form
    - url/content_length/content_type
    - request_id/metadata/source

    Source-specific notes:
    - aws:sqs: `request.text` or `request.json` reflect the SQS message body; `request.attributes` exposes `messageAttributes`.
    - aws:s3: `request.method` is the S3 operation; `request.json` includes time, bucket, type, action, key, size, eTag, sequencer.
    - aws:dynamodb: `request.method` is INSERT/MODIFY/REMOVE; `request.json` includes table, method, id, type, keys, old, new.
    - aws:lambda: Direct invocation payload via `request.json` or `request.body`.
    - aws:scheduled_event: `request.json` is the EventBridge event `detail`.
    """
    def __init__(self) -> None:
        """
        Initializes the Request instance and configures the logger to include the session ID.
        """
        self._current_request: contextvars.ContextVar[LocalRequest] = contextvars.ContextVar("current_request")
        # set logger filter to have request id
        logger.addFilter(type(
            "SessionIDFilter", 
            (logging.Filter,), 
            {"filter": lambda self, record: setattr(record, "request_id", request.request_id) or True}
        )())

    # All properties simply proxy the current LocalRequest instance
    # to make it available globally within the current execution context.

    @property
    def method(self) -> str:
        """HTTP method or event method (e.g., GET, POST, ObjectCreated, INSERT)."""
        return self._current_request.get().method

    @property
    def path(self) -> str:
        """Matched route path (without query string)."""
        return self._current_request.get().path

    @property
    def full_path(self) -> str:
        """Full path including query string (e.g., "/items?limit=10")."""
        return self._current_request.get().full_path

    @property
    def headers(self) -> Dict[str, str]:
        """Headers dict (keys case-insensitive; normalized to lowercase)."""
        return self._current_request.get().headers

    @property
    def body(self) -> Optional[bytes]:
        """Raw request body as bytes (may be binary)."""
        return self._current_request.get().body

    @property
    def text(self) -> Optional[str]:
        """UTF-8 body as text when applicable; otherwise None."""
        return self._current_request.get().text

    @property
    def form(self) -> Optional[Dict[str, Union[str, List[str]]]]:
        """Parsed URL-encoded form data, or None."""
        return self._current_request.get().form

    @property
    def query_params(self) -> Dict[str, Any]:
        """Parsed query parameters as a dict."""
        return self._current_request.get().query_params

    @property
    def path_params(self) -> Dict[str, str]:
        """Route placeholder values captured from the path."""
        return self._current_request.get().path_params

    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Parsed JSON body as a dict, or None if not JSON."""
        return self._current_request.get().json

    @property
    def url(self) -> str:
        """Full request URL (scheme, host, path, and query)."""
        return self._current_request.get().url

    @property
    def content_length(self) -> int:
        """Content-Length as an integer (0 if missing/invalid)."""
        return self._current_request.get().content_length

    @property
    def content_type(self) -> str:
        """Content-Type header value or empty string."""
        return self._current_request.get().content_type

    @property
    def request_id(self) -> str:
        """AWS request id when available; otherwise a generated id or "N/A"."""
        req = self._current_request.get(None)
        if req:
            return req.request_id
        return "N/A"

    @request_id.setter
    def request_id(self, value: str) -> None:
        self._current_request.get().request_id = value

    @property
    def metadata(self) -> Dict[str, Any]:
        """Extra metadata associated with the request (source, event, context)."""
        return self._current_request.get().metadata

    @property
    def source(self) -> Optional[str]:
        """Source identifier (e.g., aws:sqs, aws:s3, aws:dynamodb, aws:lambda)."""
        return self._current_request.get().metadata.get("source", None)

    @property
    def attributes(self) -> Dict[str, Any]:
        """Event-specific attributes; for SQS, returns `messageAttributes`."""
        return self._current_request.get().metadata.get("event", {}).get("messageAttributes", {})

    def _set(self, value: LocalRequest) -> contextvars.Token:
        """
        Internal: sets the current request context to the specified value.

        Parameters:
            value (LocalRequest): Internal request object.

        Returns:
            contextvars.Token: A token representing the previous state of the context variable, 
                            which can be used to reset it later.
        """
        return self._current_request.set(value)

    def _reset(self, token: contextvars.Token) -> None:
        """
        Internal: resets the current request context to a previous state using a context variable token.

        Parameters:
            token (contextvars.Token): The token representing the previous state of the context variable.

        Returns:
            None
        """
        self._current_request.reset(token)

request = Request()
