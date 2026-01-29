"""Base plugin abstract class for cloudx framework."""

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """Abstract base class that all cloudx plugins must inherit from.
    
    Every plugin must implement the `name()` method to be considered valid.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the unique identifier for this plugin.
        
        Returns:
            A string identifier that uniquely names this plugin instance.
        """
        pass
