"""Plugin finder for discovering plugins by type."""

import sys
import importlib.metadata
from typing import Dict, List, Optional, Any, Type
from collections import defaultdict

from .base import BasePlugin


class PluginFinder:
    """Discover and organize plugins by their type.
    
    Plugins are discovered via Python's entry-point mechanism. The entry point
    group format is ``cloudx.{type}.plugins`` where ``{type}`` is the plugin type
    (e.g., "boilerplate").
    
    Example:
        Entry point group: ``cloudx.boilerplate.plugins``
        Plugin type: ``boilerplate``
    """

    def __init__(self) -> None:
        """Initialize the finder with an empty cache."""
        self._plugins_by_type: Dict[str, List[Any]] = defaultdict(list)
        self._type_classes: Dict[str, Type[BasePlugin]] = {}

    def register_type(self, type_name: str, type_class: Type[BasePlugin]) -> None:
        """Register a plugin type class.
        
        Parameters:
            type_name: The name of the plugin type (e.g., "boilerplate").
            type_class: The abstract class that represents this plugin type.
        """
        self._type_classes[type_name] = type_class

    def find_by_type(self, plugin_type: str, interface: Optional[str] = None) -> List[Any]:
        """Find all plugins of a specific type.
        
        Parameters:
            plugin_type: The plugin type to search for (e.g., "boilerplate").
            interface: Optional method name that plugins must implement.
            
        Returns:
            A list of plugin instances of the specified type.
        """
        # Return cached plugins if available and interface matches
        if plugin_type in self._plugins_by_type and interface is None:
            return self._plugins_by_type[plugin_type]
        
        entry_point_group = f"cloudx.{plugin_type}.plugins"
        
        if sys.version_info < (3, 10):
            plugins_entry_points = importlib.metadata.entry_points().get(entry_point_group, [])
        else:
            plugins_entry_points = importlib.metadata.entry_points().select(group=entry_point_group)

        plugins = []
        for entry_point in plugins_entry_points:
            try:
                PluginClass = entry_point.load()
                plugin_obj = PluginClass()

                if self._is_valid_plugin(plugin_obj, plugin_type, interface):
                    plugins.append(plugin_obj)
                    print(f"Found plugin: {plugin_obj.name()} (type: {plugin_type})")
                else:
                    print(f"Skipped invalid plugin: {plugin_obj} (type: {plugin_type})")
            except Exception as e:
                print(f"Error loading plugin from {entry_point}: {e}")

        self._plugins_by_type[plugin_type] = plugins
        return plugins

    def find_by_type_and_name(
        self, 
        plugin_type: str, 
        plugin_name: str, 
        interface: Optional[str] = None
    ) -> Optional[Any]:
        """Find a specific plugin by type and name.
        
        Parameters:
            plugin_type: The plugin type to search in.
            plugin_name: The name of the plugin (from its ``name()`` method).
            interface: Optional interface constraint.
            
        Returns:
            The plugin instance if found, None otherwise.
        """
        # Check cache first if no interface constraint
        if plugin_type in self._plugins_by_type and interface is None:
            plugins = self._plugins_by_type[plugin_type]
        else:
            plugins = self.find_by_type(plugin_type, interface)
        for plugin in plugins:
            if plugin.name() == plugin_name:
                print(f"Found plugin: {plugin_name} (type: {plugin_type})")
                return plugin
        print(f"Plugin not found: {plugin_name} (type: {plugin_type})")
        return None

    def get_all_plugins_by_type(self) -> Dict[str, List[Any]]:
        """Get all discovered plugins organized by type.
        
        Returns:
            A dictionary mapping plugin type names to lists of plugin instances.
        """
        return dict(self._plugins_by_type)

    def _is_valid_plugin(
        self, 
        plugin: Any, 
        plugin_type: str, 
        interface: Optional[str]
    ) -> bool:
        """Validate that a plugin is valid for the given type.
        
        Parameters:
            plugin: The plugin instance to validate.
            plugin_type: The expected plugin type.
            interface: Optional interface method name.
            
        Returns:
            True if the plugin is valid, False otherwise.
        """
        # Check if plugin has name() method
        if not (hasattr(plugin, "name") and callable(getattr(plugin, "name"))):
            return False

        # Check if plugin is instance of the type class (if registered)
        if plugin_type in self._type_classes:
            type_class = self._type_classes[plugin_type]
            if not isinstance(plugin, type_class):
                return False

        # Check interface if specified
        if interface is not None:
            if not (hasattr(plugin, interface) and callable(getattr(plugin, interface))):
                return False

        return True
