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

"""Plugin management commands for Maestria."""

import shutil
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def list_plugins(config: Any) -> None:
    """List all installed Maestria plugins.

    Args:
        config: Configuration object
    """
    from maestria.plugins import discover_plugins

    plugins = discover_plugins()

    if not plugins:
        console.print("[yellow]No Maestria plugins installed.[/yellow]")
        return

    table = Table(title="Installed Maestria Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for plugin_name, plugin_class in plugins.items():
        table.add_row(plugin_name, plugin_class.description)

    console.print(table)


def create_plugin(plugin_name: str) -> None:
    """Create a new Maestria plugin project.

    This creates a new plugin project with the necessary structure and files.

    Args:
        plugin_name: Name of the plugin to create
    """
    from maestria.templates import process_template_files

    # Ensure the plugin name follows convention
    if not plugin_name.startswith("maestria-"):
        plugin_name = f"maestria-{plugin_name}"

    # Create the plugin directory
    plugin_dir = Path.cwd() / plugin_name

    if plugin_dir.exists():
        console.print(f"[yellow]Directory already exists: {plugin_dir}[/yellow]")
        if not console.input("Do you want to continue? [y/N] ").lower().startswith("y"):
            return
    else:
        plugin_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Creating Maestria plugin: {plugin_name}[/bold]")

    # Create the plugin package name
    package_name = plugin_name.replace("-", "_")
    plugin_name_short = plugin_name.replace("maestria-", "")

    # Get the path to the plugin template
    template_path = (
        Path(__file__).parent.parent / "templates" / "data" / "plugin_template"
    )

    # Copy the template to the plugin directory
    for item in template_path.iterdir():
        if item.is_dir():
            # For src directory, need special handling to handle variable substitution in the path
            if item.name == "src":
                # Create the src directory
                src_dir = plugin_dir / "src"
                src_dir.mkdir(exist_ok=True)

                # Copy contents with proper package name
                for sub_item in item.iterdir():
                    if sub_item.is_dir():
                        package_dir = src_dir / package_name
                        if sub_item.name.startswith("{{package_name}}"):
                            package_dir.mkdir(exist_ok=True)
                            for file_item in sub_item.iterdir():
                                if file_item.is_dir():
                                    shutil.copytree(
                                        file_item,
                                        package_dir / file_item.name,
                                        dirs_exist_ok=True,
                                    )
                                else:
                                    shutil.copy2(
                                        file_item, package_dir / file_item.name
                                    )
                        else:
                            pkg_dir = src_dir / sub_item.name
                            shutil.copytree(sub_item, pkg_dir, dirs_exist_ok=True)
                    else:
                        shutil.copy2(sub_item, src_dir / sub_item.name)
            else:
                shutil.copytree(item, plugin_dir / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, plugin_dir / item.name)

    # Use safe hardcoded defaults - no environment variables to prevent path traversal
    author_name = "Your Name"
    author_email = ""  # Placeholder - user should update in generated plugin

    # Process template variables
    context = {
        "plugin_name": plugin_name,
        "plugin_name_short": plugin_name_short,
        "package_name": package_name,
        "author_name": author_name,
        "author_email": author_email,
    }

    # Process all files in the plugin directory
    process_template_files(plugin_dir, context)

    console.print(f"[green]Maestria plugin created successfully at {plugin_dir}[/green]")
    console.print("To get started, run:")
    console.print(f"  cd {plugin_name}")
    console.print("  maestria env setup")
    console.print("  maestria test")


def add_plugin_commands(config: Any) -> None:
    """Add plugin management commands to the CLI.

    Args:
        config: Configuration object
    """
    import click

    from maestria.cli import cli

    @cli.group()
    def plugin():
        """Manage Maestria plugins."""
        pass

    @plugin.command(name="list")
    def plugin_list():
        """List installed plugins."""
        list_plugins(config)

    @plugin.command(name="create")
    @click.argument("name")
    def plugin_create(name: str):
        """Create a new plugin project."""
        create_plugin(name)

    return plugin
