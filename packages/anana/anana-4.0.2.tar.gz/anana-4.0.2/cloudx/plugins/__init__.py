"""Plugin system for cloudx framework."""

from .base import BasePlugin
from .types import BoilerplatePlugin
from .finder import PluginFinder
from .loader import PluginLoader

# Register the boilerplate plugin type globally
# This ensures PluginLoader instances use the registered type
_finder = PluginFinder()
_finder.register_type("boilerplate", BoilerplatePlugin)

# Monkey-patch PluginLoader to use the shared finder with registered types
_original_init = PluginLoader.__init__

def _init_with_registered_types(self):
    """Initialize PluginLoader with pre-registered types."""
    _original_init(self)
    # Copy registered types to the new instance
    for type_name, type_class in _finder._type_classes.items():
        self.finder.register_type(type_name, type_class)

PluginLoader.__init__ = _init_with_registered_types

__all__ = ["BasePlugin", "BoilerplatePlugin", "PluginFinder", "PluginLoader"]
