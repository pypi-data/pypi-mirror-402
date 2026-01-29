import os
import inspect
from functools import lru_cache

class SingletonMeta(type):
    """
    A thread-safe implementation of Singleton.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs) -> object:
        """
        Ensures that only one instance of the class is created.

        Parameters:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            object: The singleton instance of the class.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
    def reset_instance(cls) -> None:
        """
        Resets the singleton instance for the class.
        """
        """Resets the singleton instance for the class."""
        if cls in cls._instances:
            del cls._instances[cls]
                
def validate_path_params_cached(handler, path_params):
    if path_params is None:
        path_params = {}

    @lru_cache(maxsize=None)
    def get_handler_signature(handler):
        """Extracts required and all parameters from the handler signature."""
        sig = inspect.signature(handler)
        required = {
            name
            for name, param in sig.parameters.items()
            if param.default is inspect.Parameter.empty
        }
        all_params = set(sig.parameters.keys())
        required.discard("asyncify_args")
        required.discard("asyncify_kwargs")
        all_params.discard("asyncify_args")
        all_params.discard("asyncify_kwargs")

        return required, all_params

    required, all_params = get_handler_signature(handler)

    # Check for missing required parameters
    missing = required - path_params.keys()
    if missing:
        return False, f"Missing required parameters: {missing}"

    # Check for unexpected parameters
    unexpected = path_params.keys() - all_params
    if unexpected:
        return False, f"Unexpected parameters: {unexpected}"

    return True, None

def detect_platform():
    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        return "aws"
    elif "K_SERVICE" in os.environ:
        return "GCP"
    else:
        return "Unknown Platform"