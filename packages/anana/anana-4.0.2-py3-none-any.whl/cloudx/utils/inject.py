import inspect
from functools import wraps
from typing import Any, Callable, List, Union

from .container import Container

def bind(identifier: str, 
         target: Union[Callable, Any], 
         singleton: bool = False, 
         override: bool = False, 
         *args, 
         **kwargs) -> None:
    """
    Binds a service or factory to the container.

    Parameters:
        identifier (str): The unique identifier for the service.
        target (Union[Callable, Any]): The class, function, or instance to bind.
        singleton (bool): Whether the service is a singleton. Defaults to False.
        override (bool): Whether to override an existing binding. Defaults to False.
        *args: Positional arguments for service instantiation.
        **kwargs: Keyword arguments for service instantiation.

    Raises:
        Exception: If the identifier already exists and override is False.
    """
    if Container()._is_exist(identifier=identifier) and override == False:
        raise Exception("identifier " + str(identifier) + " already exist")
    if inspect.isclass(target):
        service_factory = lambda: target(*args, **kwargs)
    elif inspect.isfunction(target):
        service_factory = target
    else:
        if singleton == False:
            raise Exception("Not singleton can be only with class type or class function (lambda). please check identifier = " + str(identifier))
        service_factory = lambda: target
    Container()._register(identifier=identifier, service_factory=service_factory, singleton=singleton)

def inject(*service_names: str) -> Callable:
    """
    Decorator for injecting services into functions or class constructors.

    Parameters:
        service_names (str): The identifiers of the services to inject.

    Returns:
        Callable: The injection decorator.
    """
    if len(service_names) == 1 and callable(service_names[0]):
        # Case when decorator is used without parentheses
        target = service_names[0]
        service_names = []
        return _inject_decorator(target, service_names)
    elif len(service_names) == 1 and service_names[0] is None:
        # Case when decorator is used with None
        def decorator(target):
            return _inject_decorator(target, ())
        return decorator
    else:
        def decorator(target):
            return _inject_decorator(target, service_names)
        return decorator

def _inject_decorator(target: Callable, service_names: List[str]) -> Callable:
    """
    Helper function for the inject decorator.

    Parameters:
        target (Callable): The target function or class to decorate.
        service_names (List[str]): The list of service identifiers.

    Returns:
        Callable: The decorated function or class.
    """
    if inspect.isclass(target):
        original_init = target.__init__
        @wraps(original_init)
        def wrapped_init(self, *init_args, **init_kwargs):
            sig = inspect.signature(original_init)
            param_names = list(sig.parameters.keys())
            if "self" in param_names:
                param_names.remove("self")
            for i, param_name in enumerate(param_names):
                if param_name == "self":
                    continue
                if param_name not in init_kwargs or init_kwargs[param_name] is None:
                    if i < len(service_names):
                        init_kwargs[param_name] = Container()._resolve(service_names[i])
                    else:
                        param_type = sig.parameters[param_name].annotation
                        if param_type != inspect.Parameter.empty:
                            init_kwargs[param_name] = Container()._resolve(param_type)
            original_init(self, *init_args, **init_kwargs)
        target.__init__ = wrapped_init
        return target
    else:
        @wraps(target)
        def wrapped_function(*func_args, **func_kwargs):
            sig = inspect.signature(target)
            param_names = list(sig.parameters.keys())
            if "self" in param_names:
                param_names.remove("self") # for class methods
            for i, param_name in enumerate(param_names):
                if param_name not in func_kwargs or func_kwargs[param_name] is None:
                    if i < len(service_names):
                        func_kwargs[param_name] = Container()._resolve(service_names[i])
                    else:
                        param_type = sig.parameters[param_name].annotation
                        if param_type != inspect.Parameter.empty:
                            func_kwargs[param_name] = Container()._resolve(param_type)
            return target(*func_args, **func_kwargs)
        return wrapped_function
    
