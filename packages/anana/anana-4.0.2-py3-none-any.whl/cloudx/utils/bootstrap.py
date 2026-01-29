import os
from typing import Callable, Optional

from .container import Container

_MOCK_PROFILE = "MOCK"


def bootstrap(profile: Optional[str] = None, immediate: bool = False) -> Callable:
    """Decorator for registering bootstrap functions with optional immediate execution."""

    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        if not profile or profile in Container().profiles:
            if immediate:
                func()
                Container()._bind(func, immediate=True)
            else:
                Container()._bind(func)
        return func

    return decorator


def mock_env(env_var: str, expected_value: str) -> Callable:
    """Execute the wrapped bootstrap immediately when a mock profile is active."""

    if not isinstance(env_var, str) or not env_var:
        raise TypeError("env_var must be a non-empty string")
    if not isinstance(expected_value, str):
        raise TypeError("expected_value must be a string")

    def decorator(target: Callable[[], None]) -> Callable[[], None]:
        if os.environ.get(env_var) != expected_value:
            return target

        sanitized = os.environ.get("PROFILE", "").replace(";", ",")
        profiles = [segment.strip() for segment in sanitized.split(",") if segment.strip()]
        if _MOCK_PROFILE not in profiles:
            profiles.append(_MOCK_PROFILE)
        os.environ["PROFILE"] = ",".join(profiles)
        Container().profiles = _MOCK_PROFILE

        return bootstrap(profile=_MOCK_PROFILE, immediate=True)(target)

    return decorator
