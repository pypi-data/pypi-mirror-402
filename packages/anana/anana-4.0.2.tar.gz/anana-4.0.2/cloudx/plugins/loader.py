"""Plugin loader for executing plugins by type and name."""

from typing import Optional, Any

from .finder import PluginFinder


class PluginLoader:
    """Load and execute plugins by type and name.
    
    This class provides methods to discover, find, and execute plugins
    organized by their type.
    """

    def __init__(self) -> None:
        """Initialize the loader with a plugin finder."""
        self.finder = PluginFinder()

    def load_plugin(
        self, 
        plugin_type: str, 
        plugin_name: str, 
        interface: Optional[str] = None
    ) -> Optional[Any]:
        """Load a specific plugin by type and name.
        
        Parameters:
            plugin_type: The plugin type (e.g., "boilerplate").
            plugin_name: The plugin name (from its ``name()`` method).
            interface: Optional interface constraint.
            
        Returns:
            The plugin instance if found, None otherwise.
        """
        return self.finder.find_by_type_and_name(plugin_type, plugin_name, interface)

    def run_plugin(
        self,
        plugin_type: str,
        plugin_name: str,
        interface: Optional[str] = None,
        *args,
        **kwargs
    ) -> bool:
        """Execute a plugin by type and name.
        
        Parameters:
            plugin_type: The plugin type (e.g., "boilerplate").
            plugin_name: The plugin name (from its ``name()`` method).
            interface: Specific handler to run (e.g., "init" or "add").
                When omitted, falls back to "run" or direct call.
            *args, **kwargs: Arguments forwarded to the selected handler.
            
        Returns:
            True when a callable handler is executed successfully, otherwise False.
        """
        plugin = self.load_plugin(plugin_type, plugin_name, interface)
        if plugin is None:
            return False

        handlers = []
        if interface:
            handler = getattr(plugin, interface, None)
            if callable(handler):
                handlers.append(handler)
        
        run_handler = getattr(plugin, "run", None)
        if callable(run_handler):
            handlers.append(run_handler)
        
        if callable(plugin):
            handlers.append(plugin)

        for handler in handlers:
            try:
                result = handler(*args, **kwargs)
                return bool(result) if result is not None else True
            except Exception as e:
                print(f"Error executing plugin {plugin_name}: {e}")
                return False

        print(f"Plugin {plugin_name} (type: {plugin_type}) does not expose a callable handler for interface '{interface}'.")
        return False

    def print_all_plugins(self) -> bool:
        """Load all plugins and print them grouped by type.
        
        Returns:
            True on success, False when discovery errors occur.
        """
        try:
            # Find all plugin types (currently hardcoded to boilerplate, but extensible)
            plugin_types = ["boilerplate"]  # Can be extended to discover types dynamically
            
            all_plugins = {}
            for plugin_type in plugin_types:
                plugins = self.finder.find_by_type(plugin_type)
                if plugins:
                    all_plugins[plugin_type] = plugins

            if not all_plugins:
                print("No plugins found.")
                return True

            # Print plugins grouped by type
            for plugin_type, plugins in sorted(all_plugins.items()):
                print(f"\n{plugin_type.upper()} Plugins:")
                print("-" * (len(plugin_type) + 9))
                for plugin in plugins:
                    print(f"  - {plugin.name()}")
            
            return True
        except Exception as ex:
            print(f"Error: {ex}")
            return False

    # Backward compatibility methods (deprecated, use finder methods directly)
    def find_plugin_by_name(
        self, 
        plugin_name: str, 
        interface: Optional[str] = None
    ) -> Optional[Any]:
        """Find a plugin by name (backward compatibility).
        
        This method assumes "boilerplate" type for backward compatibility.
        For new code, use load_plugin() with explicit type.
        
        Parameters:
            plugin_name: The plugin name.
            interface: Optional interface constraint.
            
        Returns:
            The plugin instance if found, None otherwise.
        """
        return self.load_plugin("boilerplate", plugin_name, interface)
