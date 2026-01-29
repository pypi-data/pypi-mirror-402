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

"""Install command for Maestria."""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Set

from rich.console import Console
from rich.table import Table

from maestria.commands.helpers import build_uv_pip_cmd, log_command, log_result
from maestria.environment import activate_environment

console = Console()


def parse_dependencies(config: Any, dev: bool = False) -> Set[str]:
    """Parse dependencies from pyproject.toml.

    Args:
        config: Configuration object
        dev: Whether to include development dependencies

    Returns:
        Set of dependencies
    """
    dependencies = set(config.dependencies)

    if dev:
        dependencies.update(set(config.dev_dependencies))

    return dependencies


def check_installed_packages(
    project_dir: Path, venv_path: Optional[Path] = None, verbose: bool = False
) -> Dict[str, str]:
    """Get installed packages in the environment.

    Args:
        project_dir: Path to the project directory
        venv_path: Optional virtual environment path
        verbose: Whether to show verbose output

    Returns:
        Dictionary of installed packages with versions
    """
    try:
        # Use uv pip list to get installed packages
        venv = venv_path if venv_path else project_dir / ".venv"
        cmd = build_uv_pip_cmd("list", "--python", str(venv), "--format", "json")
        log_command(cmd, cwd=project_dir, description="Checking installed packages")
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        log_result(result)

        # Parse JSON output
        import json

        packages_list = json.loads(result.stdout.strip())
        # Convert list of {"name": "pkg", "version": "1.0"} to dict {"pkg": "1.0"}
        installed_packages = {pkg["name"]: pkg["version"] for pkg in packages_list}
        return installed_packages

    except Exception as e:
        if verbose:
            console.print(f"[red]Error checking installed packages: {str(e)}[/red]")
        return {}


def install_dependencies(
    config: Any,
    dev: bool = False,
    update: bool = False,
    editable: bool = True,
    verbose: bool = False,
) -> bool:
    """Install dependencies.

    This installs dependencies from pyproject.toml in the virtual environment.
    By default, it also installs the current package in editable mode.

    Args:
        config: Configuration object
        dev: Whether to install development dependencies
        update: Whether to update existing packages
        editable: Whether to install the current package in editable mode
        verbose: Whether to show detailed output

    Returns:
        True if successful, False otherwise
    """
    project_dir = Path(config.root_dir)

    # Step 1: Activate environment (done once at the beginning)
    try:
        activate_environment(project_dir, venv_path=config.venv_path, verbose=verbose)
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print(
            "[red]Virtual environment not found. Please run 'maestria env setup' first.[/red]"
        )
        return False

    # Step 2: Get dependencies from configuration
    dependencies = parse_dependencies(config, dev=dev)
    if not dependencies and not editable:
        console.print(
            "[yellow]No dependencies found in pyproject.toml and editable install disabled.[/yellow]"
        )
        return True

    # Step 3: Check what's already installed
    installed_packages = check_installed_packages(
        project_dir, venv_path=config.venv_path, verbose=verbose
    )

    # Create a table to display installation info
    table = Table(title="Installing dependencies")
    table.add_column("Package", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Result", style="yellow")

    # Step 4: Install or update packages using uv pip
    uv_pip_cmd_base = build_uv_pip_cmd("install", "--python", str(config.venv_path))

    # First install the current package in editable mode if requested
    if editable:
        console.print("[bold]Installing current package in editable mode...[/bold]")
        try:
            cmd = uv_pip_cmd_base + ["--editable", "."]
            log_command(
                cmd, cwd=project_dir, description="Installing project in editable mode"
            )
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                check=True,
                capture_output=not verbose,
                text=True,
            )
            log_result(result)
            table.add_row(f"{project_dir.name}", "Install (editable)", "✓")
        except subprocess.CalledProcessError as e:
            console.print(
                f"[yellow]Warning: Could not install package in editable mode: {str(e)}[/yellow]"
            )
            table.add_row(f"{project_dir.name}", "Install (editable)", "✗ Failed")

    # Determine the installation command
    if update:
        uv_pip_cmd = uv_pip_cmd_base + ["--upgrade"]
        action = "Update"
    else:
        uv_pip_cmd = uv_pip_cmd_base
        action = "Install"

    # Install all dependencies at once
    console.print(
        f"[bold]{'Installing' if not update else 'Updating'} {'development' if dev else ''} dependencies...[/bold]"
    )

    # Build dependency list for display
    deps_to_install = []
    for dep in dependencies:
        # Check if already installed and we're not updating
        dep_name = (
            dep.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("<")[0]
            .split(">")[0]
            .strip()
        )
        # Convert keys to lowercase for case-insensitive comparison
        lowercase_keys = [k.lower() for k in installed_packages.keys()]
        if not update and dep_name.lower() in lowercase_keys:
            table.add_row(
                dep,
                "Skip (already installed)",
                f"v{installed_packages.get(dep_name, 'unknown')}",
            )
            continue

        deps_to_install.append(dep)

    if not deps_to_install and editable:
        console.print(
            "[green]All dependencies are already installed. Package is installed in editable mode.[/green]"
        )
        console.print(table)
        return True
    elif not deps_to_install:
        console.print("[green]All dependencies are already installed.[/green]")
        console.print(table)
        return True

    # Install the dependencies
    try:
        cmd = uv_pip_cmd + deps_to_install
        log_command(
            cmd,
            cwd=project_dir,
            description=f"Installing {len(deps_to_install)} dependencies",
        )
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=not verbose,
            text=True,
        )
        log_result(result)

        # Verify installation
        updated_packages = check_installed_packages(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )

        for dep in deps_to_install:
            dep_name = (
                dep.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("<")[0]
                .split(">")[0]
                .strip()
            )
            # Convert keys to lowercase for case-insensitive comparison
            lowercase_keys = [k.lower() for k in updated_packages.keys()]
            if dep_name.lower() in lowercase_keys:
                table.add_row(
                    dep, action, f"✓ v{updated_packages.get(dep_name, 'unknown')}"
                )
            else:
                table.add_row(dep, action, "✗ Failed")

        console.print(table)
        console.print("[green]Dependencies installed successfully![/green]")
        return True

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to install dependencies:[/red] {str(e)}")

        for dep in deps_to_install:
            table.add_row(dep, action, "✗ Failed")

        console.print(table)
        return False
