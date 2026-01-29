# Copyright 2024-2025 eBay Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Plugin system for Maestria."""

import importlib
import importlib.metadata
from abc import ABC
from typing import Any, Callable, Dict, List, Type

from rich.console import Console

console = Console()


class MaestriaPlugin(ABC):
    """Base class for Maestria plugins."""

    name: str = "base"
    description: str = "Base plugin"

    @classmethod
    def get_commands(cls) -> Dict[str, Callable]:
        """Get plugin commands.

        Returns:
            A dictionary of command name -> command function
        """
        return {}

    @classmethod
    def get_hooks(cls) -> Dict[str, List[Callable]]:
        """Get plugin hooks.

        Returns:
            A dictionary of hook name -> list of hook functions
        """
        return {}

    @classmethod
    def initialize(cls) -> None:
        """Initialize the plugin."""
        pass


# Dictionary to store discovered plugins
_plugins: Dict[str, Type[MaestriaPlugin]] = {}
_commands: Dict[str, Callable] = {}
_hooks: Dict[str, List[Callable]] = {}


def discover_plugins() -> Dict[str, Type[MaestriaPlugin]]:
    """Discover all installed Maestria plugins.

    Returns:
        Dictionary of plugin name -> plugin class
    """
    global _plugins

    if not _plugins:
        # Discover plugins via entry points using importlib.metadata
        try:
            # Use importlib.metadata for entry point discovery
            try:
                # For Python 3.10+
                eps = importlib.metadata.entry_points(group="maestria.plugins")
                eps = list(eps)
            except TypeError:
                # For older versions (Python 3.8-3.9)
                all_eps = importlib.metadata.entry_points()
                eps = [
                    ep
                    for ep in all_eps
                    if getattr(ep, "group", None) == "maestria.plugins"
                ]

            for entry_point in eps:
                try:
                    # Load plugin using importlib.metadata entry point
                    plugin_class = entry_point.load()
                    if issubclass(plugin_class, MaestriaPlugin):
                        _plugins[entry_point.name] = plugin_class
                        console.print(
                            f"[dim]Discovered plugin: {entry_point.name}[/dim]"
                        )
                except Exception as e:
                    console.print(
                        f"[yellow]Error loading plugin {entry_point.name}: {str(e)}[/yellow]"
                    )
        except Exception as e:
            console.print(f"[yellow]Error discovering plugins: {str(e)}[/yellow]")

        # Initialize all discovered plugins
        for plugin_name, plugin_class in _plugins.items():
            try:
                plugin_class.initialize()
            except Exception as e:
                console.print(
                    f"[yellow]Error initializing plugin {plugin_name}: {str(e)}[/yellow]"
                )

    return _plugins


def get_plugin_commands() -> Dict[str, Callable]:
    """Get commands from all plugins.

    Returns:
        Dictionary of command name -> command function
    """
    global _commands

    if not _commands:
        plugins = discover_plugins()
        for plugin_name, plugin_class in plugins.items():
            try:
                plugin_commands = plugin_class.get_commands()
                for cmd_name, cmd_func in plugin_commands.items():
                    if cmd_name in _commands:
                        console.print(
                            f"[yellow]Warning: Command '{cmd_name}' from plugin '{plugin_name}' "
                            f"overrides an existing command[/yellow]"
                        )
                    _commands[cmd_name] = cmd_func
            except Exception as e:
                console.print(
                    f"[yellow]Error getting commands from plugin {plugin_name}: {str(e)}[/yellow]"
                )

    return _commands


def get_plugin_hooks() -> Dict[str, List[Callable]]:
    """Get hooks from all plugins.

    Returns:
        Dictionary of hook name -> list of hook functions
    """
    global _hooks

    if not _hooks:
        plugins = discover_plugins()
        for plugin_name, plugin_class in plugins.items():
            try:
                plugin_hooks = plugin_class.get_hooks()
                for hook_name, hook_funcs in plugin_hooks.items():
                    if not isinstance(hook_funcs, list):
                        hook_funcs = [hook_funcs]

                    if hook_name not in _hooks:
                        _hooks[hook_name] = []

                    _hooks[hook_name].extend(hook_funcs)
            except Exception as e:
                console.print(
                    f"[yellow]Error getting hooks from plugin {plugin_name}: {str(e)}[/yellow]"
                )

    return _hooks


def run_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """Run all hooks for a given hook name.

    Args:
        hook_name: The name of the hook to run
        *args: Arguments to pass to the hook functions
        **kwargs: Keyword arguments to pass to the hook functions

    Returns:
        List of results from hook functions
    """
    hooks = get_plugin_hooks()
    results = []

    if hook_name in hooks:
        for hook in hooks[hook_name]:
            try:
                result = hook(*args, **kwargs)
                results.append(result)
            except Exception as e:
                console.print(
                    f"[yellow]Error running hook '{hook_name}': {str(e)}[/yellow]"
                )

    return results
