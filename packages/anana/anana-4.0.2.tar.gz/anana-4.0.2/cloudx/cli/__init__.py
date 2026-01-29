import argparse
from typing import Optional, List
from ..plugins import PluginLoader

def help_command() -> bool:
    """Print a concise overview of the available CLI commands.

    The output mirrors the top-level usage summary users see when the CLI is invoked
    without arguments, making it easy to discover the core subcommands and any optional
    plugin hooks without consulting external documentation.
    """
    print("Usage:  cloudx [COMMAND] [OPTIONS]")
    print()
    print("Fast, simple and lightweight ASGI framework for building cloud native microservices")
    print()
    print("Commands:")
    print("  init       Create a new project boilerplate")
    print("  add        Add new services to an existing project")
    print("  plugins    Display all installed plugins grouped by type")
    print("  version    Display the current version of cloudx")
    print("  help       Display this help information")
    print()
    print("Command Options:")
    print()
    print("  init")
    print("    --project PROJECT              Name of the project to create (required)")
    print("    --services SERVICE [SERVICE]   List of service names to create (required)")
    print("    --plugin PLUGIN                Plugin name to use instead of default 'cloudx'")
    print()
    print("  add")
    print("    --services SERVICE [SERVICE]   List of service names to add (required)")
    print("    --plugin PLUGIN                Plugin name to use instead of default 'cloudx'")
    print()
    print("Examples:")
    print("  # Initialize a new project with multiple services")
    print("  cloudx init --project my-project --services api-service db-service")
    print()
    print("  # Initialize with custom plugin")
    print("  cloudx init --project my-project --services api-service --plugin custom-plugin")
    print()
    print("  # Add services to an existing project")
    print("  cloudx add --services new-service1 new-service2")
    print()
    print("  # Add services with a custom plugin")
    print("  cloudx add --services new-service --plugin custom-plugin")
    print()
    print("  # Display version")
    print("  cloudx version")
    print()
    print("  # List all installed plugins")
    print("  cloudx plugins")
    print()
    return True

def version_command() -> bool:
    """Display the installed cloudx version.

    Reads the version from the installed package metadata.
    """
    try:
        # Try importlib.metadata (Python 3.8+)
        try:
            from importlib.metadata import version
            package_version = version("cloudx")
        except ImportError:
            # Fallback for Python 3.7 (requires importlib-metadata package)
            try:
                from importlib_metadata import version  # type: ignore
                package_version = version("cloudx")
            except ImportError:
                # Final fallback: try reading from VERSION file if available
                from pathlib import Path
                version_file = Path(__file__).parent.parent.parent / "VERSION"
                if version_file.exists():
                    package_version = version_file.read_text().strip()
                else:
                    print("Error: Could not determine version. Install importlib-metadata for Python 3.7.")
                    return False
        
        print(f"Version: {package_version}")
        return True
    except Exception as e:
        print(f"Error: Failed to get version. {e}")
        return False
    
def plugins_command() -> bool:
    """List the names of all discovered cloudx plugins.

    Behind the scenes the `PluginLoader` scans the `cloudx.boilerplate.plugins` entry-point group and
    prints each plugin's declared name so teams can confirm what extensions are available.
    """
    try:
        return PluginLoader().print_all_plugins()
    except Exception as e:
        print(f"Error: Failed to get plugins. {e}")
        return False
    
def init_command(
    project_name: str, 
    services: List[str], 
    plugin_name: Optional[str] = None
) -> bool:
    """Generate the default project boilerplate and optionally invoke a plugin hook.

    The built-in scaffolding always runs first to ensure the project structure exists. If a
    plugin name is provided the loader looks for an `init` handler on that plugin and runs
    it so custom templates or automation can build on top of the base layout. If no plugin
    name is provided, the default "cloudx" plugin is used.
    
    Args:
        project_name: The name of the project to create.
        services: List of service names to create.
        plugin_name: Optional plugin name to use instead of default.
    """
    # Use default plugin if no plugin name provided
    plugin_to_run = plugin_name if plugin_name else "cloudx"
    
    loader = PluginLoader()
    plugin = loader.load_plugin("boilerplate", plugin_to_run)
    if plugin is None:
        print(f"Failed to load plugin '{plugin_to_run}'. \033[1mMake sure the plugin {plugin_to_run} is installed.\033[0m")
        return False
    
    # Step 1: Call set_project first
    if hasattr(plugin, "set_project") and callable(getattr(plugin, "set_project")):
        try:
            result = plugin.set_project(project_name)
            if result is False:
                return False
        except Exception as e:
            print(f"Error calling set_project: {e}")
            return False
    
    # Step 2: Call set_service for each service, then update_project
    for service in services:
        if hasattr(plugin, "set_service") and callable(getattr(plugin, "set_service")):
            try:
                plugin.set_service(service)
            except Exception as e:
                print(f"Error calling set_service for '{service}': {e}")
                return False
        
        # Call update_project after each set_service with the service name
        if hasattr(plugin, "update_project") and callable(getattr(plugin, "update_project")):
            try:
                result = plugin.update_project(service)
                if result is False:
                    return False
            except Exception as e:
                print(f"Error calling update_project for '{service}': {e}")
                return False
    
    return True

def add_command(services: List[str], plugin_name: Optional[str] = None) -> bool:
    """Scaffold a new service using the built-in templates and optional plugin logic.

    The standard generator creates files inside the project's `apps/` directory. When a
    plugin name is supplied, the loader executes that plugin's `add` handler afterwards so
    additional provisioning or customization can run in the same workflow. If no plugin
    name is provided, the default "cloudx" plugin is used.
    
    Args:
        services: List of service names to add.
        plugin_name: Optional plugin name to use instead of default.
    """
    # Use default plugin if no plugin name provided
    plugin_to_run = plugin_name if plugin_name else "cloudx"
    
    loader = PluginLoader()
    plugin = loader.load_plugin("boilerplate", plugin_to_run)
    if plugin is None:
        print(f"Failed to load plugin '{plugin_to_run}'. \033[1mMake sure the plugin {plugin_to_run} is installed.\033[0m")
        return False
    
    # Call set_service for each service, then update_project
    for service in services:
        if hasattr(plugin, "set_service") and callable(getattr(plugin, "set_service")):
            try:
                plugin.set_service(service)
            except Exception as e:
                print(f"Error calling set_service for '{service}': {e}")
                return False
        
        # Call update_project after each set_service with the service name
        if hasattr(plugin, "update_project") and callable(getattr(plugin, "update_project")):
            try:
                result = plugin.update_project(service)
                if result is False:
                    return False
            except Exception as e:
                print(f"Error calling update_project for '{service}': {e}")
                return False
    
    return True

def main(args: Optional[List[str]] = None) -> bool:
    """The entry point for the cloudx CLI tool."""
    known_commands = {"help": help_command, 
                    "version": version_command, "plugins": plugins_command}

    parser = argparse.ArgumentParser(description="cloudx tools")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("help", help="display detailed help information")
    subparsers.add_parser("version", help="display installed cloudx version")
    subparsers.add_parser("plugins", help="display installed cloudx plugins")
    init_parser = subparsers.add_parser("init", help="create a new project boilerplate")
    init_parser.add_argument("--project", required=True, help="name of the project to create")
    init_parser.add_argument("--services", required=True, nargs="+", help="list of service names to create")
    init_parser.add_argument("--plugin", help="optional plugin name to run instead of the default template")
    add_parser = subparsers.add_parser("add", help="add a new service to the project")
    add_parser.add_argument("--services", required=True, nargs="+", help="list of service names to add")
    add_parser.add_argument("--plugin", help="optional plugin name to run after adding the service")
    if args is None:
        import sys
        args = sys.argv[1:]

    args = parser.parse_args(args)
    if args.command is None:
        return help_command()
    if args.command == "init":
        return init_command(
            project_name=args.project,
            services=args.services,
            plugin_name=getattr(args, "plugin", None)
        )
    if args.command == "add":
        return add_command(
            services=args.services,
            plugin_name=getattr(args, "plugin", None)
        )
    return known_commands[args.command]()
