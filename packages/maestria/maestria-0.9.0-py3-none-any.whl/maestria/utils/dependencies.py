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

"""Dependency management utilities for Maestria."""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

from maestria.utils import get_venv_bin_dir, normalize_venv_path

logger = logging.getLogger(__name__)


def check_dependencies(
    project_dir: Path, venv_path: Path, verbose: bool = False
) -> Tuple[bool, List[str]]:
    """Check if required dependencies for release are installed.

    Args:
        project_dir: Path to the project directory
        venv_path: Path to the virtual environment (relative or absolute)
        verbose: Whether to show verbose output

    Returns:
        Tuple of (all_installed, missing_dependencies)
    """
    # Make venv_path absolute relative to project_dir if needed
    venv_path = normalize_venv_path(project_dir, venv_path)
    if verbose:
        logger.info("Checking dependencies in verbose mode")
        logger.debug(f"Current sys.executable: {sys.executable}")
        logger.debug(f"VENV_PATH: {venv_path}")

    modules_to_check = ["pytest", "build", "twine"]
    cli_tools_to_check = ["bump2version"]
    missing_deps = []

    for module in modules_to_check:
        spec = importlib.util.find_spec(module)
        if verbose:
            logger.debug(f"Module {module}: found={spec is not None}")
        if spec is None:
            missing_deps.append(module)

    for tool in cli_tools_to_check:
        venv_bin = get_venv_bin_dir(venv_path)
        tool_script_path = venv_bin / tool
        if verbose:
            logger.debug(
                f"Checking {tool} at: {tool_script_path}, exists={tool_script_path.exists()}"
            )

        if not tool_script_path.exists():
            missing_deps.append(tool)

    return (len(missing_deps) == 0, missing_deps)


def verify_dependencies(
    project_dir: Path, venv_path: Path, dependencies: List[str], verbose: bool = False
) -> Tuple[bool, List[str]]:
    """Verify that dependencies were successfully installed.

    Args:
        project_dir: Path to the project directory
        venv_path: Path to the virtual environment (relative or absolute)
        dependencies: List of dependencies to verify
        verbose: Whether to show verbose output

    Returns:
        Tuple of (all_verified, still_missing)
    """
    # Make venv_path absolute relative to project_dir if needed
    venv_path = normalize_venv_path(project_dir, venv_path)
    modules_to_check = ["pytest", "build", "twine"]
    cli_tools_to_check = ["bump2version"]
    missing_deps = []

    for module in modules_to_check:
        if module in dependencies:
            spec = importlib.util.find_spec(module)
            if verbose:
                logger.debug(f"Module {module}: found={spec is not None}")
            if spec is None:
                missing_deps.append(module)

    for tool in cli_tools_to_check:
        if tool in dependencies:
            venv_bin = get_venv_bin_dir(venv_path)
            tool_script_path = venv_bin / tool
            if verbose:
                logger.debug(
                    f"Checking {tool} at: {tool_script_path}, exists={tool_script_path.exists()}"
                )

            if not tool_script_path.exists():
                import shutil

                tool_path = shutil.which(tool)
                if verbose:
                    logger.debug(f"CLI tool {tool}: shutil.which result={tool_path}")
                if tool_path is None:
                    missing_deps.append(tool)

    return (len(missing_deps) == 0, missing_deps)


def main():
    """CLI entry point for dependency checking."""
    logging.basicConfig(
        level=(
            logging.DEBUG if os.environ.get("MAESTRIA_VERBOSE") == "1" else logging.INFO
        ),
        format="%(message)s",
    )

    project_dir = Path.cwd()
    venv_path = Path(os.environ.get("VENV_PATH", ".venv"))
    all_installed, missing = check_dependencies(project_dir, venv_path, verbose=True)

    print(",".join(missing))

    if not all_installed:
        for dep in missing:
            logger.info(f"DEBUG_INFO: Missing dependency: {dep}")


if __name__ == "__main__":
    main()
