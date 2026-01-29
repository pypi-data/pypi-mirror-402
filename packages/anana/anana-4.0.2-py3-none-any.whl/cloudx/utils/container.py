import os
from typing import Any, Callable, List, Set, Union

from ..common import SingletonMeta


class Container(metaclass=SingletonMeta):
    """Service container responsible for dependency registration and resolution."""

    def __init__(self) -> None:
        self._profiles = self._parse_profiles(os.environ.get("PROFILE", ""))
        self._service_factories = {}
        self._singletons = {}
        self._bootstraps: List[Callable[[], None]] = []
        self._binded = False
        self._teardowns: Set[Callable[[Any], None]] = set()

    @staticmethod
    def _parse_profiles(raw_profile: str) -> List[str]:
        if not raw_profile:
            return []
        sanitized = raw_profile.replace(";", ",")
        return [segment.strip() for segment in sanitized.split(",") if segment.strip()]

    @property
    def profiles(self) -> List[str]:
        return list(self._profiles)

    @profiles.setter
    def profiles(self, value: Union[str, List[str]]) -> None:
        if isinstance(value, str):
            parsed = self._parse_profiles(value)
        elif isinstance(value, list):
            parsed = [segment.strip() for segment in value if isinstance(segment, str) and segment.strip()]
        else:
            raise TypeError("profiles must be assigned a string or list of strings")

        for profile in parsed:
            if profile not in self._profiles:
                self._profiles.append(profile)

    def _bind(self, func: Callable[[], None], immediate: bool = False) -> None:
        if not immediate:
            self._bootstraps.append(func)
            self._binded = False

    def _register(self, identifier: str, service_factory: Callable[[], Any], singleton: bool = False) -> None:
        self._service_factories[identifier] = (service_factory, singleton)

    def _is_exist(self, identifier: str) -> bool:
        return identifier in self._service_factories

    def _resolve(self, identifier: str) -> Any:
        if self._binded is False:
            run_bootstraps: List[Callable[[], None]] = []
            for func in list(self._bootstraps):
                try:
                    func()
                    run_bootstraps.append(func)
                except Exception:
                    self._bootstraps.remove(func)
                    raise
            for bootstrap in run_bootstraps:
                self._bootstraps.remove(bootstrap)
            self._binded = True

        if identifier in self._singletons:
            return self._singletons[identifier]

        factory, singleton = self._service_factories.get(identifier, (None, None))
        if factory is None:
            raise ValueError(f"Service factory '{identifier}' not found")

        service = factory()
        if singleton:
            self._singletons[identifier] = service
        return service

    def _register_teardown(self, func: Callable[[Any], None]) -> None:
        self._teardowns.add(func)

    @property
    def teardowns(self) -> List[Callable[[Any], None]]:
        return list(self._teardowns)
