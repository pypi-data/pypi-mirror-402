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

"""Environment management commands for Maestria."""

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from maestria.commands.helpers import (
    build_uv_pip_cmd,
    log_command,
    log_result,
    run_uv_cmd,
)

console = Console()


def is_module_installed(module_name: str) -> bool:
    """Check if a module is installed.

    Args:
        module_name: The name of the module to check

    Returns:
        True if the module is installed, False otherwise
    """
    return importlib.util.find_spec(module_name) is not None


def run_with_venv_activation(
    cmd: List[str], venv_path: str, cwd: str, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """Run a command with virtual environment activation.

    Args:
        cmd: Command to run
        venv_path: Path to virtual environment
        cwd: Working directory
        env: Optional environment variables

    Returns:
        CompletedProcess instance
    """
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Clone the current environment
    merged_env = os.environ.copy()

    # Add custom environment variables
    if env:
        merged_env.update(env)

    # Set up the virtual environment activation
    is_windows = platform.system() == "Windows"
    venv_bin = os.path.join(venv_path, "Scripts" if is_windows else "bin")

    # Update PATH to prioritize the virtual environment
    path_sep = ";" if is_windows else ":"
    merged_env["PATH"] = f"{venv_bin}{path_sep}{merged_env.get('PATH', '')}"

    # Set VIRTUAL_ENV environment variable
    merged_env["VIRTUAL_ENV"] = venv_path

    if verbose:
        full_cmd = " ".join(cmd)
        console.print(f"[dim]Running command in virtual environment: {full_cmd}[/dim]")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=merged_env,
            check=True,
            capture_output=True,
            text=True,
        )

        if verbose and result.stdout:
            console.print(f"[dim]Command output:\n{result.stdout.strip()}[/dim]")

        return result
    except subprocess.CalledProcessError as e:
        if verbose and e.stderr:
            console.print(f"[dim]Command error output:\n{e.stderr.strip()}[/dim]")
        raise


def setup_environment(config: Any) -> None:
    """Set up the development environment.

    This creates a virtual environment using uv and installs dependencies.

    Args:
        config: Configuration object
    """
    project_dir = Path(config.root_dir)
    venv_path = Path(config.venv_path)

    # Create a table to display environment info
    table = Table(title="Setting up environment")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Step 1: Create virtual environment
    console.print("[bold]Creating virtual environment...[/bold]")
    try:
        run_uv_cmd(
            "venv",
            str(venv_path),
            "--python",
            config.python_version,
            cwd=project_dir,
            description="Creating virtual environment",
        )
        table.add_row("Virtual environment", "✓ Created")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to create virtual environment:[/red] {e.stderr}")
        table.add_row("Virtual environment", "✗ Failed")
        console.print(table)
        return
    except FileNotFoundError:
        console.print("[red]UV not found.[/red]")
        console.print("Maestria requires UV (Ultraviolet) to function properly.")
        console.print(
            "Please install UV using: [bold]pip install uv[/bold] or visit: https://github.com/astral-sh/uv"
        )
        table.add_row("Virtual environment", "✗ Failed - UV required")
        console.print(table)
        return

    # Step 2: Install dependencies
    console.print("[bold]Installing dependencies...[/bold]")

    try:
        # Install project dependencies using uv
        cmd = build_uv_pip_cmd("install", "--python", str(venv_path), "-e", ".")
        log_command(
            cmd, cwd=project_dir, description="Installing project in editable mode"
        )
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        log_result(result)

        table.add_row("Dependencies", "✓ Installed")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to install dependencies:[/red]\n{e.stderr}")
        table.add_row("Dependencies", "✗ Failed")
        console.print(table)
        return

    # Step 3: Install dev dependencies
    console.print("[bold]Installing development dependencies...[/bold]")
    try:
        # Install development dependencies using uv
        cmd = build_uv_pip_cmd("install", "--python", str(venv_path), "-e", ".[dev]")
        log_command(
            cmd, cwd=project_dir, description="Installing project with dev extras"
        )
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        log_result(result)

        table.add_row("Development dependencies", "✓ Installed")
    except subprocess.CalledProcessError as e:
        console.print(
            f"[yellow]Warning: Failed to install development dependencies:[/yellow]\n{e.stderr}"
        )
        table.add_row("Development dependencies", "✗ Failed")

    # Scripts are no longer used - Maestria now uses direct Python calls
    table.add_row("Common scripts", "N/A (using direct calls)")

    # Display summary
    console.print(table)
    console.print("[green]Environment setup completed successfully![/green]")
    console.print("You can now run commands using: [bold]maestria run <command>[/bold]")


def update_environment(config: Any) -> None:
    """Update the development environment.

    This updates dependencies in the virtual environment.

    Args:
        config: Configuration object
    """
    project_dir = Path(config.root_dir)

    # Get virtual environment path
    venv_path = Path(config.venv_path)

    # Check if the virtual environment exists
    if not venv_path.exists():
        console.print(
            "[yellow]Virtual environment not found. Creating it first...[/yellow]"
        )
        setup_environment(config)
        return

    # Step 1: Update dependencies
    console.print("[bold]Updating dependencies...[/bold]")
    try:
        # Run the installation scripts to update dependencies
        # Update regular dependencies using uv
        cmd = build_uv_pip_cmd(
            "install", "--python", str(venv_path), "--upgrade", "-e", "."
        )
        log_command(
            cmd, cwd=project_dir, description="Upgrading all project dependencies"
        )
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        log_result(result)

        # Update development dependencies using uv
        cmd = build_uv_pip_cmd(
            "install", "--python", str(venv_path), "--upgrade", "-e", ".[dev]"
        )
        log_command(
            cmd, cwd=project_dir, description="Upgrading all development dependencies"
        )
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        log_result(result)

        console.print("[green]Dependencies updated successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to update dependencies:[/red] {e.stderr}")
        return


def show_environment_info(config: Any) -> None:
    """Show information about the current environment.

    Args:
        config: Configuration object
    """
    project_dir = Path(config.root_dir)
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Create a table to display environment info
    table = Table(title="Environment Information")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="green")

    # Check if .venv exists
    venv_path = Path(config.venv_path)
    venv_exists = venv_path.exists()

    # Get the bin/Scripts directory path
    if venv_exists:
        venv_bin_path = venv_path / "bin"
        if not venv_bin_path.exists():  # Windows
            venv_bin_path = venv_path / "Scripts"

        venv_python = venv_bin_path / "python"
        if sys.platform == "win32":
            venv_python = venv_python.with_suffix(".exe")

    # Get Python version
    python_version = sys.version.split()[0]
    table.add_row("System Python version", python_version)

    # Check if UV is installed
    try:
        uv_version = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        table.add_row("UV version", uv_version)
    except (subprocess.CalledProcessError, FileNotFoundError):
        table.add_row("UV status", "[yellow]Not installed[/yellow]")

    # Get virtual environment info
    if venv_exists:
        table.add_row("Virtual environment path", str(venv_path.absolute()))
    else:
        table.add_row("Virtual environment path", "[yellow]Not found[/yellow]")

    venv_active_path = os.environ.get("VIRTUAL_ENV")
    if venv_active_path:
        table.add_row("Active virtual environment", venv_active_path)
    else:
        table.add_row("Active virtual environment", "[yellow]Not activated[/yellow]")

    # Get Python version in the virtual environment
    if venv_exists and venv_python.exists():
        try:
            venv_python_version = subprocess.run(
                [str(venv_python), "--version"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            table.add_row("Venv Python version", venv_python_version)
        except subprocess.CalledProcessError:
            table.add_row("Venv Python version", "[yellow]Could not determine[/yellow]")

    # Get installed packages in the venv
    if venv_exists:
        try:
            # Use uv pip list instead of python -m pip list
            # This works even if pip isn't installed in the venv
            result = subprocess.run(
                ["uv", "pip", "list", "--python", str(venv_path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            installed_packages = result.stdout.strip()

            # Extract package count
            # uv pip list format:
            # Line 1: Header (Package  Version ...)
            # Line 2: Dashes (------  ------- ...)
            # Line 3+: Packages
            # If no packages, output is just: "Using Python X.X.X environment at: ..."
            lines = installed_packages.split("\n")
            if len(lines) >= 3 and "---" in lines[1]:
                # Has proper header format
                package_count = len(lines) - 2
            else:
                # No packages installed or different format
                package_count = 0
            table.add_row("Installed packages", f"{package_count} packages")

            # Get packages from pyproject.toml dependencies
            declared_packages = []
            if config.dependencies:
                for dep in config.dependencies:
                    # Extract package name from dependency spec (e.g., "click>=8.1.0" -> "click")
                    pkg_name = (
                        dep.split(">")[0]
                        .split("<")[0]
                        .split("=")[0]
                        .split("[")[0]
                        .strip()
                    )
                    declared_packages.append(pkg_name)

            # Add dev dependencies if they exist
            if hasattr(config, "dev_dependencies") and config.dev_dependencies:
                for dep in config.dev_dependencies:
                    pkg_name = (
                        dep.split(">")[0]
                        .split("<")[0]
                        .split("=")[0]
                        .split("[")[0]
                        .strip()
                    )
                    if pkg_name not in declared_packages:
                        declared_packages.append(pkg_name)

            if verbose:
                # Show all packages
                for line in installed_packages.split("\n")[2:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            table.add_row(parts[0], parts[1])
            else:
                # Show only packages declared in pyproject.toml
                for pkg_name in declared_packages:
                    # Search case-insensitively
                    pkg_lower = pkg_name.lower()
                    if f"\n{pkg_lower} " in installed_packages.lower():
                        pkg_line = [
                            line
                            for line in installed_packages.split("\n")
                            if line.lower().startswith(f"{pkg_lower} ")
                            or line.lower().startswith(f"{pkg_lower}\t")
                        ]
                        if pkg_line:
                            pkg_version = pkg_line[0].split()[1]
                            table.add_row(pkg_name, pkg_version)
        except subprocess.CalledProcessError:
            table.add_row("Installed packages", "[yellow]Could not determine[/yellow]")

    # Get project info from config (already parsed from pyproject.toml)
    if config.path and config.path.exists():
        table.add_row("Project configuration", "pyproject.toml ✓")
        table.add_row("Project name", config.name)
        table.add_row("Project version", config.version)
    else:
        table.add_row(
            "Project configuration", "[yellow]pyproject.toml not found[/yellow]"
        )

    # Display the table
    console.print(table)
