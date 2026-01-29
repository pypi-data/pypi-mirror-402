import re
from typing import Callable, List, Dict, Union, Optional, Tuple, Any
from .response import ClientErrors
from ..common import SingletonMeta 
from ..methods import Method

class Router(metaclass=SingletonMeta):
    """
    A singleton router for handling route matching and registration in an ASGI application.
    """

    def __init__(self) -> None:
        """
        Initializes the Router with an empty list of routes.
        """
        self.routes: List[Tuple[re.Pattern, Optional[List[str]], Dict, Callable]] = []

    def add_route(self, 
                  path: str, 
                  method: Union[str, List[str]] = None, 
                  handler: Callable = None, 
                  **extra: Dict[str, Any]) -> None:
        """
        Adds a route to the router.

        Parameters:
            path (str): The path for the route, which can include parameters (e.g., "/users/{id}").
            method (Union[str, List[str]]): The HTTP methods allowed for this route (e.g., "GET", "POST").
            handler (Callable): The handler function for the route.
            **extra (Dict[str, Any]): Additional configuration for the route.
        """
        extra = extra["extra"]
        path_regex = re.compile(self.__convert_path_to_regex(path))
        self.routes.append((path_regex, method, extra, handler))

    def match(self, 
              path: str, 
              method: Optional[str] = None) -> Tuple[Optional[Callable], Optional[Dict[str, str]], Dict[str, Any]]:
        """
        Matches a path and HTTP method to a registered route.

        Parameters:
            path (str): The request path to match.
            method (Optional[str]): The HTTP method to match. Defaults to None.

        Returns:
            Tuple[Optional[Callable], Optional[Dict[str, str]], Dict[str, Any]]:
                - Callable: The handler function if a match is found, otherwise a client error response.
                - Dict[str, str]: The extracted path parameters if a match is found, otherwise an empty dictionary.
                - Dict[str, Any]: Additional configuration for the matched route.
        """
        method = Method[method]
        allowed_methods = set()
        path_params, config = {}, {}
        
        # Iterate through all routes to find a match
        for path_regex, methods, route_config, handler in self.routes:
            match = path_regex.match(path)
            if match:
                route_path_params = match.groupdict() or None
                # Store path_params and config from matching routes for error responses
                # Keep updating config so we have the latest matching route's config
                path_params = route_path_params or {}
                config = route_config
                # Collect allowed methods for this path
                if methods:
                    # Handle both list and string (for UNKNOWNMETHOD case)
                    if isinstance(methods, list):
                        allowed_methods.update(methods)
                    else:
                        allowed_methods.add(methods)
                # Check if this route matches both path and method
                if method is None:
                    return handler, route_path_params, route_config
                elif methods:
                    # Handle both list and string (for UNKNOWNMETHOD case)
                    if isinstance(methods, list) and method in methods:
                        return handler, route_path_params, route_config
                    elif not isinstance(methods, list) and method == methods:
                        return handler, route_path_params, route_config
        
        # If path matched but method didn't, return method not allowed
        if allowed_methods:
            return ClientErrors.method_not_allowed(allowed_methods), path_params, config
        
        # For SQS paths that don't match, check if any SQS route has batch enabled
        # This preserves the original behavior where config from matching routes was available
        if path.startswith("/sqs/"):
            for path_regex, methods, route_config, handler in self.routes:
                if path_regex.pattern.startswith("^/sqs/") and route_config.get("partial_batch_response_enabled", "False") == "True":
                    config = route_config
                    break
        
        return ClientErrors.not_found(), path_params, config
    
    def __convert_path_to_regex(self, path: str) -> str:
        """
        Converts a route path to a regular expression.

        Parameters:
            path (str): The route path to convert (e.g., "/users/{id}" or "/<url:re:.+>").

        Returns:
            str: A regular expression string that matches the given path pattern.
        """
        # Convert custom regex patterns <param:re:pattern>
        path = re.sub(r"<(\w+):re:([^>]+)>", r"(?P<\1>\2)", path)

        # Convert * to match any number of characters but only within a single segment
        path = re.sub(r"\*", "[^/]*", path)  # Match any sequence of characters except "/"

        # Convert wildcard path parameters {param:path} to named groups (?P<param>.*)
        path = re.sub(r"\{(\w+):path\}", r"(?P<\1>.*)", path)

        # Convert regular path parameters {param} to named groups (?P<param>[^/]+)
        path = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)

        return f"^{path}$"
