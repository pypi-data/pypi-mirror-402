import json
from typing import Callable, Dict, Any, Optional, List, Union
from decimal import Decimal
from datetime import datetime

HTTP_STATUS_DESC = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
    }

def default_json_serializer(obj):
    """Default serializer for JSON encoding that handles special types."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class Response:
    """
    ASGI response object for returning data from controllers.

    - Infers `content_type` from `content` when not provided:
      dict/list/int/float/bool/Decimal/None → application/json; bytes → application/octet-stream; str → text/plain.
    - Serializes content to bytes based on the chosen `content_type`.
    - Ensures a Content-Type header is present; preserves any provided headers.

    Example:
        @app.get("/health")
        def health():
            return Response({"status": "ok"})
    """

    def __init__(self, 
                 content: Any, 
                 status_code: int = 200, 
                 headers: Optional[Dict[str, str]] = None, 
                 content_type: Optional[str] = None) -> None:
        """
        Initializes a Response instance.

        Parameters:
            - `content` (Any): Response payload (dict/list/str/bytes/number/bool/None).
            - `status_code` (int): HTTP status code. Default: 200.
            - `headers` (Optional[Dict[str, str] | List[tuple]]): Additional headers to include.
              Either a dict of string headers or a pre-encoded ASGI-style list of (name: bytes, value: bytes) tuples.
            - `content_type` (Optional[str]): Explicit content type; if omitted, inferred from `content`.
        """
        self._status_code = status_code
        self._content = content
        self._content_type = content_type or self._infer_content_type(content)
        self._headers = headers or {}

    def _infer_content_type(self, content: Any) -> str:
        """
        Infers the content type based on the type of the content.

        Parameters:
            content (Any): The response content.

        Returns:
            str: The inferred content type.
        """
        if isinstance(content, (dict, list, int, float, bool, Decimal)) or content is None:
            return "application/json"  # JSON content
        elif isinstance(content, bytes):
            return "application/octet-stream"  # Binary data
        elif isinstance(content, str):
            return "text/plain"  # isinstance(content, str)
        else:
            return "application/json"  # Default Fallback to JSON for unknown types
        
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """
        Sends the HTTP response using the ASGI protocol.

        Parameters:
            - `scope` (Dict[str, Any]): ASGI scope.
            - `receive` (Callable): ASGI receive callable.
            - `send` (Callable): ASGI send callable.

        Notes:
            - If headers lack Content-Type, it is added from `content_type`.
            - Accepts headers as dict[str, str] or list[(bytes, bytes)].
        """
        if isinstance(self._headers, Dict):
            if not any(k.lower() == "content-type" for k in self._headers.keys()):
                content_type = [(b"content-type", self.content_type.encode())]
            else:
                content_type = []
            headers = content_type + [(k.encode(), v.encode()) for k, v in self._headers.items()]
        elif isinstance(self._headers, list):
            if not any(k.lower() == "content-type" for k, _ in self._headers):
                content_type = [(b"content-type", self.content_type.encode())]
            else:
                content_type = []
            headers = content_type + self._headers
        else:
            headers = []
        
        await send({
            "type": "http.response.start",
            "status": self.status,
            "headers": headers
        })
        await send({
            "type": "http.response.body",
            "body": self.body,
            "more_body": False
        })

    @property
    def status(self) -> int:
        """Returns the HTTP status code."""
        return self._status_code
    
    @property
    def status_code(self) -> int:
        """Gets or sets the HTTP status code."""
        return self._status_code

    @status_code.setter
    def status_code(self, status_code: int) -> None:
        self._status_code = status_code
    
    @property
    def status_line(self) -> str:
        """Returns the status line (e.g., "200 OK")."""
        return f"{self.status} {Response.description(self.status)}"

    @property
    def content(self) -> Any:
        """Gets or sets the raw content value without serialization."""
        return self._content

    @content.setter
    def content(self, value: Any) -> None:
        self._content = value

    @property
    def body(self) -> bytes:
        """Serialized response body as bytes based on `content_type`."""
        if self._content is None:
            return b"null" if self.content_type == "application/json" else b""
            
        if isinstance(self._content, bytes):
            return self._content
            
        if self.content_type == "application/json":
            if isinstance(self._content, bool):
                return b"true" if self._content else b"false"
                
            if isinstance(self._content, (int, float)):
                return str(self._content).encode()
                
            if isinstance(self._content, Decimal):
                return str(float(self._content)).encode()
                
            if isinstance(self._content, (dict, list)):
                return json.dumps(self._content, default=default_json_serializer).encode()
                
            try:
                return json.dumps(self._content, default=default_json_serializer).encode()
            except (TypeError, json.JSONDecodeError):
                return str(self._content).encode()
                
        # For non-JSON content types
        return str(self._content).encode()
    
    @property
    def text(self) -> Optional[str]:
        """
        Convenience view of content as text.

        - str: returned as-is
        - dict/list: JSON string
        - bool/number/Decimal: string representation
        - bytes: decoded as UTF-8 (or None if undecodable)
        - None: ""
        """
        if isinstance(self._content, str):
            return self._content
        if isinstance(self._content, (dict, list)):
            return json.dumps(self._content, default=default_json_serializer, indent=2)
        if isinstance(self._content, bool):  # Add explicit boolean handling
            return str(self._content).lower()  # Returns "true" or "false"
        if isinstance(self._content, (int, float, Decimal)):  # Handle numbers
            return str(self._content)
        if self._content is None:
            return ""  # Empty string for None
        if isinstance(self._content, bytes):
            try:
                return self._content.decode()
            except UnicodeDecodeError:
                return None
        if self._content is None:
            return None
        return str(self._content)

    @property
    def json(self) -> Optional[Union[dict, list, str, bool, int, float, Decimal, datetime]]:
        """
        Convenience view of content as JSON-friendly Python value.

        - dict/list: returned as-is
        - str: parsed as JSON when valid
        - bool/number/Decimal/datetime: converted to JSON-compatible types
        - bytes: decoded then parsed when valid
        - other: best-effort JSON serialization; returns None if not possible
        """
        if isinstance(self._content, (dict, list)): # If already dict/list, return as is
            return self._content
        if isinstance(self._content, str): # If string, try to parse as JSON
            try:
                return json.loads(self._content)
            except json.JSONDecodeError:
                pass
        if isinstance(self._content, bool):  # Add explicit boolean handling
            return self._content  # Return bool directly for JSON
        if isinstance(self._content, (bool, int, float)):  # Handle numbers directly
            return self._content
        if isinstance(self._content, Decimal):  # Convert Decimal to float for JSON
            return float(self._content)
        if isinstance(self._content, datetime):  # Convert datetime to ISO format string
            return self._content.isoformat()
        if isinstance(self._content, bytes): # If bytes, try to decode and parse as JSON
            try:
                return json.loads(self._content.decode())
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
        if self._content is None:
            return None  # Returns Python None, which becomes JSON null
        try: # Try to serialize anything else that might be JSON-serializable
            return json.loads(json.dumps(self._content, default=default_json_serializer))
        except (TypeError, json.JSONDecodeError):
            return None

    @property
    def headers(self) -> Dict[str, str]:
        """Gets or sets string HTTP headers as a dict."""
        return self._headers

    @headers.setter
    def headers(self, headers: Dict[str, str]) -> None:
        self._headers = headers

    def add_header(self, key: str, value: str) -> None:
        """Adds a single header to the response."""
        self._headers[key] = value
    
    def add_headers(self, headers: Dict[str, str]) -> None:
        """Adds multiple headers to the response."""
        if isinstance(self._headers, Dict):
            self._headers.update(headers)

    @property
    def content_type(self) -> str:
        """Gets or sets the Content-Type value used for serialization and headers."""
        return self._content_type

    @content_type.setter
    def content_type(self, content_type: str) -> None:
        self._content_type = content_type
    
    @property
    def content_length(self) -> int:
        """Returns the length in bytes of the serialized response body."""
        if self.body is None:
            return 0
        return len(self.body)
    
    @staticmethod
    def description(status: int) -> str:
        """Returns the HTTP status text for the given status code."""
        return HTTP_STATUS_DESC.get(status, "Unknown Status")

class ClientErrors:
    """
    Helpers for generating 4xx HTTP responses.

    - `handle_4xx`: Sends a plain-text error response with the given status.
    - `method_not_allowed`: Returns a 405 response including an `Allow` header.
    - `not_found`: Returns a 404 response.
    """

    async def handle_4xx(scope: Dict[str, Any], 
                         receive: Callable, 
                         send: Callable, 
                         ex: Optional[Exception] = None, 
                         error_code: int = 500) -> None:
        """Sends a 4xx error response."""
        response = Response(
            content=Response.description(error_code),
            status_code=error_code,
            content_type="text/plain",
            headers=scope["extra"]
        )
        await response(scope, receive, send)

    @staticmethod
    def method_not_allowed(allowed_methods: List[str]) -> Callable[[], Response]:
        """Returns a 405 Method Not Allowed response with the allowed methods."""
        def handler(**kwargs) -> Response:
            """Handler that accepts **kwargs to ignore path_params when called from core."""
            status_code=405
            return Response(status_code=status_code, content=Response.description(status_code), 
                            content_type="text/plain", headers=[(b"Allow", ", ".join(allowed_methods).encode())])
        return handler
    
    @staticmethod
    def not_found() -> Callable[[], Response]:
        """Returns a 404 Not Found response."""
        def handler(**kwargs) -> Response:
            """Handler that accepts **kwargs to ignore path_params when called from core."""
            status_code=404
            return Response(status_code=status_code, content=Response.description(status_code), content_type="text/plain")
        return handler
    
class ServerErrors:
    """Helpers for generating 5xx HTTP responses."""

    async def handle_5xx(scope: Dict[str, Any], 
                         receive: Callable, 
                         send: Callable, 
                         ex: Optional[Exception] = None, 
                         error_code: int = 500) -> None:
        """Sends a 5xx error response."""
        response = Response(
            content=Response.description(error_code),
            status_code=error_code,
            content_type="text/plain",
            headers=scope["extra"]
        )
        await response(scope, receive, send)
