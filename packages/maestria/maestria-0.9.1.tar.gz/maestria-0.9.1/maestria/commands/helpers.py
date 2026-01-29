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

"""Helper utilities for Maestria commands.

This module provides abstractions for common command patterns:
- UV command building
- Verbose logging
- Command execution with logging
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from rich.console import Console

from maestria.utils import get_uv_index_args

console = Console()


def is_verbose() -> bool:
    """Check if verbose mode is enabled.

    Returns:
        True if MAESTRIA_VERBOSE environment variable is set to "1"
    """
    return os.environ.get("MAESTRIA_VERBOSE") == "1"


def vlog(message: str, prefix: str = "→") -> None:
    """Print a verbose log message with consistent formatting.

    Only prints if verbose mode is enabled. Uses dim styling with arrow prefix.

    Args:
        message: The message to log
        prefix: The prefix character/string (default: "→")

    Example:
        vlog("Command: uv pip install package")
        vlog("Working directory: /path/to/dir")
    """
    if is_verbose():
        console.print(f"[dim]{prefix} {message}[/dim]")


def build_uv_cmd(*args: Union[str, Path]) -> List[str]:
    """Build a UV command with consistent formatting.

    Args:
        *args: Command arguments (e.g., "pip", "install", "-e", ".")

    Returns:
        List of command parts with "uv" prefix

    Example:
        build_uv_cmd("venv", ".venv")  # ["uv", "venv", ".venv"]
        build_uv_cmd("pip", "install", "-e", ".")  # ["uv", "pip", "install", "-e", "."]
    """
    return ["uv"] + [str(arg) for arg in args]


def build_uv_pip_cmd(
    *args: Union[str, Path], include_index_urls: bool = True
) -> List[str]:
    """Build a UV pip command with consistent formatting.

    Args:
        *args: Pip command arguments (e.g., "install", "-e", ".")
        include_index_urls: Whether to include index URLs from pip.conf (default: True)

    Returns:
        List of command parts with "uv pip" prefix

    Example:
        build_uv_pip_cmd("install", "-e", ".")  # ["uv", "pip", "install", "-e", "."]
        build_uv_pip_cmd("list", "--format", "json")  # ["uv", "pip", "list", "--format", "json"]
    """
    cmd = ["uv", "pip"] + [str(arg) for arg in args]

    if include_index_urls:
        index_args = get_uv_index_args()
        if index_args:
            cmd.extend(index_args)

    return cmd


def cmd_to_string(cmd: List[Union[str, Path]]) -> str:
    """Convert a command list to a readable string.

    Args:
        cmd: List of command parts

    Returns:
        Space-separated string representation

    Example:
        cmd_to_string(["uv", "pip", "install", "."]) # "uv pip install ."
    """
    return " ".join(str(c) for c in cmd)


def log_command(
    cmd: List[Union[str, Path]],
    cwd: Optional[Path] = None,
    description: Optional[str] = None,
) -> None:
    """Log command execution details in verbose mode.

    Logs the command, working directory, and optional description
    using consistent formatting.

    Args:
        cmd: The command to log
        cwd: Working directory (optional)
        description: Human-readable description of what the command does (optional)

    Example:
        log_command(
            ["uv", "pip", "install", "-e", "."],
            cwd=Path("/path/to/project"),
            description="Installing project in editable mode"
        )
    """
    if not is_verbose():
        return

    vlog(f"Command: {cmd_to_string(cmd)}")
    if cwd:
        vlog(f"Working directory: {cwd}")
    if description:
        vlog(description)


def log_result(result: subprocess.CompletedProcess) -> None:
    """Log the result of a command execution in verbose mode.

    Args:
        result: The completed process result

    Example:
        result = subprocess.run(...)
        log_result(result)
    """
    if not is_verbose():
        return

    if result.stdout and result.stdout.strip():
        vlog(f"Output: {result.stdout.strip()}")

    if result.stderr and result.stderr.strip():
        vlog(f"Error output: {result.stderr.strip()}")


def run_uv_cmd(
    *args: Union[str, Path],
    cwd: Optional[Path] = None,
    description: Optional[str] = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a UV command with automatic logging in verbose mode.

    This combines command building, logging, execution, and result logging.

    Args:
        *args: UV command arguments
        cwd: Working directory (optional)
        description: Description of what the command does (optional)
        check: Whether to raise CalledProcessError on failure (default: True)
        capture_output: Whether to capture stdout/stderr (default: True)

    Returns:
        CompletedProcess result

    Raises:
        subprocess.CalledProcessError: If check=True and command fails

    Example:
        run_uv_cmd("venv", ".venv", cwd=project_dir, description="Creating virtual environment")
        run_uv_cmd("pip", "install", "-e", ".", cwd=project_dir, description="Installing project")
    """
    cmd = build_uv_cmd(*args)
    log_command(cmd, cwd=cwd, description=description)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture_output,
        text=True,
    )

    log_result(result)
    return result
