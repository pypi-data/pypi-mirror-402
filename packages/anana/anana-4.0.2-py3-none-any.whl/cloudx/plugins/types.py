"""Plugin type classes for cloudx framework."""

from abc import ABC, abstractmethod
from typing import Optional, Any

from .base import BasePlugin


class BoilerplatePlugin(BasePlugin, ABC):
    """Abstract plugin type for boilerplate plugins.
    
    This class represents the "boilerplate" plugin type. All boilerplate plugins
    must inherit from this class. The entry point group for this type is
    ``cloudx.boilerplate.plugins``.
    
    All boilerplate plugins must implement the ``init`` and ``add`` interfaces.
    """

    @abstractmethod
    def set_project(self, *args, **kwargs) -> Any:
        """Initialize the plugin.
        
        This method is called when the plugin is used with the ``init`` command.
        
        Args:
            *args: Positional arguments passed to the plugin.
            **kwargs: Keyword arguments passed to the plugin.
            
        Returns:
            Any value indicating success or failure. Non-falsy values indicate success.
        """
        pass

    @abstractmethod
    def set_service(self, *args, **kwargs) -> Any:
        """Add functionality to the project.
        
        This method is called when the plugin is used with the ``add`` command.
        
        Args:
            *args: Positional arguments passed to the plugin.
            **kwargs: Keyword arguments passed to the plugin.
            
        Returns:
            Any value indicating success or failure. Non-falsy values indicate success.
        """
        pass

    @abstractmethod
    def update_project(self, *args, **kwargs) -> Any:
        """Update the project.
        
        This method is called when the plugin is used with the ``update`` command.
        
        Args:
            *args: Positional arguments passed to the plugin.
            **kwargs: Keyword arguments passed to the plugin.
            
        Returns:
            Any value indicating success or failure. Non-falsy values indicate success.
        """
        pass