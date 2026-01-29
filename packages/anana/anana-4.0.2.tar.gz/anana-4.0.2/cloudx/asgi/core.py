import inspect
import os
import sys
from contextlib import contextmanager, nullcontext
from typing import Callable, Awaitable, List, Union, Dict, Any
from ..utils.logger import logger
import importlib.util
from .request import LocalRequest, request
from .response import ClientErrors, Response, ServerErrors
from ..common import SingletonMeta, validate_path_params_cached
from ..methods import Method
from .router import Router
from ..utils.teardown import schedule_teardowns
from ..utils.container import Container


@contextmanager
def _scoped_package(package_name: str, package_root: str):
    if not package_name or not package_root:
        yield
        return

    package_root = os.path.abspath(package_root)
    if not os.path.isdir(package_root):
        yield
        return

    parent = os.path.dirname(package_root)

    saved_modules: Dict[str, Any] = {}
    prefix = package_name + "."
    for name in list(sys.modules.keys()):
        if name == package_name or name.startswith(prefix):
            saved_modules[name] = sys.modules.pop(name)

    added_path = None
    if parent not in sys.path:
        sys.path.insert(0, parent)
        added_path = parent

    try:
        yield
    finally:
        for name in list(sys.modules.keys()):
            if name == package_name or name.startswith(prefix):
                module = sys.modules[name]
                module_file = getattr(module, "__file__", None)
                module_paths = getattr(module, "__path__", [])
                try:
                    collected_paths = list(module_paths) if module_paths else []
                except Exception:
                    collected_paths = []
                rooted = False
                if module_file and os.path.abspath(module_file).startswith(package_root):
                    rooted = True
                else:
                    for p in collected_paths:
                        if os.path.abspath(p).startswith(package_root):
                            rooted = True
                            break
                if rooted:
                    sys.modules.pop(name, None)

        for name, module in saved_modules.items():
            sys.modules[name] = module

        if added_path is not None:
            try:
                sys.path.remove(added_path)
            except ValueError:
                pass


class ASGICore(metaclass=SingletonMeta):
    """
    Represents an ASGI application with routing, event handling, and dynamic service loading.
    """

    def __init__(self) -> None:
        """
        Initializes the ASGI application.

        Attributes:
            _services_loaded (bool): Tracks whether the services have been loaded.
            _event_source (EventSource): The source for application events.
        """
        self._services_loaded = False

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """
        Handles incoming ASGI requests based on the scope type.

        Parameters:
            scope (Dict[str, Any]): The ASGI connection scope.
            receive (Callable): The callable to receive incoming messages.
            send (Callable): The callable to send outgoing messages.

        Raises:
            NotImplementedError: If the scope type is unsupported.
            Exception: If an error occurs while processing the request.
        """
        if scope["type"] == "http":
            m = Method[scope["method"]] 
            handler, path_params, extra = Router().match(scope["path"].rstrip("/"), m)
            scope["extra"] = extra
            local_request = await LocalRequest.from_scope(scope, receive, path_params)
            token = request._set(local_request)
            try:
                if handler is None:
                    await ServerErrors.handle_5xx(scope, receive, send, None, 501)
                else:
                    if inspect.iscoroutinefunction(handler):
                        if path_params:
                            response = await handler(**path_params)
                        else:
                            response = await handler()
                    else:
                        if path_params:
                            response = handler(**path_params)
                        else:
                            response = handler()
                    if not callable(response):
                        response_obj = Response(content=response)
                    else:
                        response_obj = response
                    await response_obj(scope, receive, send)
                    
                    # Schedule teardowns after successful response
                    container = Container()
                    teardowns = list(container.teardowns)
                    if teardowns:
                        schedule_teardowns(teardowns, local_request, response_obj, request_id=None)
            except Exception as ex:
                valid_params, reason = validate_path_params_cached(handler, path_params)
                if not valid_params:
                    logger.exception(reason)
                    await ClientErrors.handle_4xx(scope, receive, send, reason, 400)
                else:
                    reason = f"An error occurred while processing the request. ex = {ex}"
                    logger.exception(reason, exc_info=True)
                    await ServerErrors.handle_5xx(scope, receive, send, ex)
            finally:
                request._reset(token)
        else:
            raise NotImplementedError(f"Unsupported scope type: {scope['type']}")

    def boot(self, directory: Union[str, List[str]] = None) -> None:
        """
        Loads Python services dynamically from the specified directory or directories.

        Parameters:
            directory (Union[str, List[str]]): The directory or list of directories to load services from.
                                              If not specified, it uses the caller's directory.

        Raises:
            Exception: If any service file causes an exception during loading.
        """
        if directory is None:
            caller_frame = inspect.stack()[1]
            caller_file = caller_frame.filename
            directory = os.path.dirname(os.path.abspath(caller_file))
        
        if self._services_loaded:
            return
            
        self._services_loaded = True
        
        # Convert single directory to list for consistent processing
        if isinstance(directory, str):
            directories = [directory]
        else:
            directories = list(directory) if directory else []

        directories = list(dict.fromkeys(os.path.abspath(dir_path) for dir_path in directories))
        if not directories:
            return

        try:
            common_root = os.path.commonpath(directories)
        except ValueError:
            common_root = None

        def _module_matches(name: str, absolute_path: str) -> bool:
            existing_module = sys.modules.get(name)
            if existing_module is None:
                return False
            existing_spec = getattr(existing_module, "__spec__", None)
            origin = getattr(existing_spec, "origin", None) if existing_spec else None
            module_file = getattr(existing_module, "__file__", None)
            module_path = origin or module_file
            if not module_path:
                return False
            return os.path.abspath(module_path) == absolute_path

        dir_suffix_cache: Dict[str, str] = {}
        basename_counts: Dict[str, int] = {}
        if len(directories) > 1:
            for path in directories:
                basename = os.path.basename(path.rstrip(os.sep))
                basename_counts[basename] = basename_counts.get(basename, 0) + 1

        for dir_path in directories:
            basename = os.path.basename(dir_path.rstrip(os.sep))
            alias_package = None
            alias_root = None

            if basename_counts.get(basename, 0) > 1 and os.path.isdir(dir_path):
                alias_package = basename
                alias_root = dir_path

            walk_root = dir_path
            context = _scoped_package(alias_package, alias_root) if alias_package else nullcontext()

            with context:
                # Debug guard (optional logging)
                for root, _, files in os.walk(walk_root):
                    for file in files:
                        if not file.endswith(".py") or file == "__init__.py":
                            continue

                        file_path = os.path.join(root, file)
                        relative_module_path = os.path.splitext(os.path.relpath(file_path, walk_root))[0]
                        module_name = relative_module_path.replace(os.sep, ".")
                        if alias_package and not module_name.startswith(alias_package + "."):
                            module_name = f"{alias_package}.{module_name}"
                        if not module_name:
                            continue
                        absolute_file_path = os.path.abspath(file_path)
                        target_module_name = module_name
                        existing = sys.modules.get(target_module_name)
                        if existing is not None:
                            if _module_matches(target_module_name, absolute_file_path):
                                del sys.modules[target_module_name]
                            else:
                                suffix = dir_suffix_cache.get(dir_path)
                                if suffix is None:
                                    if common_root:
                                        suffix_source = os.path.relpath(dir_path, common_root)
                                    else:
                                        suffix_source = os.path.abspath(dir_path)
                                    import hashlib  # Lazy import – only used when collisions occur
                                    digest = hashlib.sha1(suffix_source.encode("utf-8")).hexdigest()[:8]
                                    if digest and digest[0].isdigit():
                                        digest = f"_{digest}"
                                    suffix = digest or "_"
                                    dir_suffix_cache[dir_path] = suffix
                                index = 1
                                target_module_name = f"{module_name}__{suffix}"
                                while True:
                                    existing = sys.modules.get(target_module_name)
                                    if existing is None:
                                        break
                                    if _module_matches(target_module_name, absolute_file_path):
                                        del sys.modules[target_module_name]
                                        break
                                    index += 1
                                    target_module_name = f"{module_name}__{suffix}__{index}"
                        try:
                            spec = importlib.util.spec_from_file_location(target_module_name, file_path)
                            if spec is None or spec.loader is None:
                                raise ImportError(f"Unable to load spec for module: {target_module_name}")
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[target_module_name] = module
                            spec.loader.exec_module(module)
                        except Exception as e:
                            logger.exception(f"Error loading service file: {file_path}")
                            raise e

    def reboot(self, directory: str) -> None:
        """
        Reloads Python services dynamically from the specified directory.

        Parameters:
            directory (str): The directory to reload services from.
        """
        self._services_loaded = False
        from .router import Router
        Router.reset_instance()
        self.boot(directory=directory)
        
    def route(self, 
              path: str, 
              methods: Union[str, List[str]] = None, 
              callback: Callable[[], Awaitable[Union[str, bytes]]] = None, 
              **extra) -> Callable:
        """
        Registers a route in the ASGI application.

        Parameters:
            path (str): The route path.
            methods (Union[str, List[str]]): The HTTP methods allowed for the route. Defaults to None.
            callback (Callable): The callback function for the route. Defaults to None.
            **extra: Additional metadata for the route.
            
            Available methods: "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"
        Returns:
            Callable: The decorator to register the route.
        """
        if isinstance(methods, str):
            methods = [methods]
        methods = [Method[m] for m in methods] if methods else Method["UNKNOWNMETHOD"]
        
        def wrapper(handler: Callable[[], Awaitable[Union[str, bytes]]]):
            Router().add_route(path=path.rstrip("/"), method=methods, handler=handler, extra=extra)
            return handler
        return wrapper(callback) if callback else wrapper
