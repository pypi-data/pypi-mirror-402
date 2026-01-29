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

"""Environment activation and validation utilities for Maestria."""

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console

from maestria.security import (
    SecurityError,
    sanitize_environment,
    validate_executable,
    validate_path,
)

console = Console()


def activate_environment(
    project_dir: Union[str, Path],
    venv_path: Optional[Union[str, Path]] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Activate and validate the Python virtual environment.

    This function ensures the virtual environment exists, activates it, and
    validates that required dependencies are installed. It's a common entry point
    for all Maestria commands that need the environment.

    Args:
        project_dir: The project directory
        venv_path: Path to the virtual environment. If None, defaults to .venv in project_dir
        verbose: Whether to display verbose output

    Returns:
        A dictionary with environment information:
        - venv_path: Path to the virtual environment
        - python_path: Path to the Python executable
        - env_variables: Environment variables for commands

    Raises:
        RuntimeError: If environment setup or activation fails
    """
    try:
        project_dir = validate_path(project_dir, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        raise RuntimeError(f"Invalid project directory: {e}") from e

    # Resolve venv_path
    if venv_path is None:
        venv_path = project_dir / ".venv"
    else:
        venv_path = Path(venv_path)
        # If relative path, make it relative to project_dir
        if not venv_path.is_absolute():
            venv_path = project_dir / venv_path

    try:
        venv_path = validate_path(venv_path, allow_absolute=True)
    except SecurityError as e:
        raise RuntimeError(f"Invalid virtual environment path: {e}") from e

    # Check if virtual environment exists
    if not venv_path.exists():
        console.print("[red]Error: Virtual environment not found.[/red]")
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )
        raise RuntimeError("Virtual environment not found")

    # Determine the bin/Scripts directory
    is_windows = platform.system() == "Windows"
    venv_bin_path = venv_path / ("Scripts" if is_windows else "bin")

    if not venv_bin_path.exists():
        console.print("[red]Error: Invalid virtual environment structure.[/red]")
        raise RuntimeError("Invalid virtual environment structure")

    # Get the Python executable
    python_path = venv_bin_path / f"python{'.exe' if is_windows else ''}"

    if not python_path.exists():
        console.print(
            "[red]Error: Python executable not found in virtual environment.[/red]"
        )
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )
        raise RuntimeError("Python executable not found in virtual environment")

    try:
        python_path = validate_executable(python_path, allowed_dirs=[venv_bin_path])
    except SecurityError as e:
        console.print(
            f"[red]Error: Security validation failed for Python executable: {e}[/red]"
        )
        raise RuntimeError(f"Invalid Python executable: {e}") from e

    # Setup environment variables for commands - sanitize first
    env_variables = sanitize_environment(os.environ.copy())

    # Update PATH to prioritize the virtual environment
    path_sep = ";" if is_windows else ":"
    env_variables["PATH"] = f"{venv_bin_path}{path_sep}{env_variables.get('PATH', '')}"

    # Set VIRTUAL_ENV environment variable
    env_variables["VIRTUAL_ENV"] = str(venv_path)

    return {
        "venv_path": venv_path,
        "python_path": python_path,
        "env_variables": env_variables,
    }


def run_in_environment(
    command: List[str],
    project_dir: Union[str, Path],
    venv_path: Optional[Union[str, Path]] = None,
    verbose: bool = False,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command in the activated virtual environment.

    Args:
        command: The command to run
        project_dir: The project directory
        venv_path: Path to the virtual environment. If None, defaults to .venv in project_dir
        verbose: Whether to display verbose output
        check: Whether to check the return code
        capture_output: Whether to capture command output

    Returns:
        A CompletedProcess instance

    Raises:
        RuntimeError: If environment activation fails
    """
    try:
        project_dir = validate_path(project_dir, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        raise RuntimeError(f"Invalid project directory: {e}") from e

    # Activate the environment
    env_info = activate_environment(project_dir, venv_path=venv_path, verbose=verbose)

    # Validate command executable if it's a path
    if command and len(command) > 0:
        cmd_executable = Path(command[0])
        if cmd_executable.exists():
            try:
                venv_bin_path = env_info["venv_path"] / (
                    "Scripts" if platform.system() == "Windows" else "bin"
                )
                validate_executable(cmd_executable, allowed_dirs=[venv_bin_path])
            except SecurityError as e:
                console.print(
                    f"[yellow]Warning: Command executable validation: {e}[/yellow]"
                )

    # Run the command
    if verbose:
        console.print(
            f"[dim]Running command in virtual environment: {' '.join(str(c) for c in command)}[/dim]"
        )

    result = subprocess.run(
        command,
        cwd=project_dir,
        env=env_info["env_variables"],
        check=check,
        capture_output=capture_output,
        text=True,
    )

    if verbose and result.stdout and capture_output:
        console.print(f"[dim]Command output:\n{result.stdout}[/dim]")

    return result
