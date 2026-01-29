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

"""Version bumping utilities for Maestria."""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from maestria.security import SecurityError, validate_executable, validate_path
from maestria.utils import get_venv_executable, normalize_venv_path
from maestria.utils.version import get_version_from_pyproject

logger = logging.getLogger(__name__)


def bump_version(
    project_dir: Path, venv_path: Path, bump_type: str, verbose: bool = False
) -> Optional[Tuple[str, str]]:
    """Bump the project version using bump2version.

    Args:
        project_dir: Path to the project directory
        venv_path: Path to the virtual environment (relative or absolute)
        bump_type: Type of version bump (patch, minor, major)
        verbose: Whether to show verbose output

    Returns:
        Tuple of (old_version, new_version) or None if failed
    """
    # Validate project_dir
    try:
        project_dir = validate_path(project_dir, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        logger.error(f"Invalid project directory: {e}")
        return None

    # Make venv_path absolute relative to project_dir if it's not already absolute
    venv_path = normalize_venv_path(project_dir, venv_path)

    # Validate venv_path
    try:
        venv_path = validate_path(venv_path, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        logger.error(f"Invalid virtual environment path: {e}")
        return None

    # Try with .exe extension first on Windows, fallback to no extension
    bump_bin = get_venv_executable(venv_path, "bump2version", ".exe")
    if not bump_bin.exists():
        bump_bin = get_venv_executable(venv_path, "bump2version", None)

    if not bump_bin.exists():
        logger.error(f"bump2version not found at {bump_bin}")
        return None

    # Validate the bump2version executable
    try:
        is_windows = platform.system() == "Windows"
        venv_bin_path = venv_path / ("Scripts" if is_windows else "bin")
        bump_bin = validate_executable(bump_bin, allowed_dirs=[venv_bin_path])
    except SecurityError as e:
        logger.error(f"Security validation failed for bump2version: {e}")
        return None

    old_version = get_version_from_pyproject(project_dir)

    # Validate bump_type to prevent command injection
    valid_bump_types = {"major", "minor", "patch"}
    if bump_type not in valid_bump_types:
        logger.error(
            f"Invalid bump type: {bump_type}. Must be one of: {valid_bump_types}"
        )
        return None

    if verbose:
        logger.info(f"Running: {bump_bin} {bump_type}")

    try:
        if verbose:
            subprocess.run(
                [str(bump_bin), bump_type],
                cwd=str(project_dir),
                check=True,
            )
        else:
            subprocess.run(
                [str(bump_bin), bump_type],
                cwd=str(project_dir),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"bump2version failed: {e}")
        return None

    new_version = get_version_from_pyproject(project_dir)

    if new_version and old_version:
        logger.info(f"Version bumped: {old_version} -> {new_version}")
        return (old_version, new_version)

    return None


def main():
    """CLI entry point for version bumping."""
    import argparse

    parser = argparse.ArgumentParser(description="Bump project version")
    parser.add_argument(
        "bump_type", choices=["patch", "minor", "major"], help="Type of version bump"
    )
    args = parser.parse_args()

    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(message)s"
    )

    # Use default .venv path - no need for environment variable
    venv_path = Path(".venv")
    project_dir = Path.cwd()

    result = bump_version(project_dir, venv_path, args.bump_type, verbose)

    if result:
        old_version, new_version = result
        print(f"BUMP_RESULT:{old_version}:{new_version}")
        sys.exit(0)
    else:
        logger.error("Failed to bump version")
        sys.exit(1)


if __name__ == "__main__":
    main()
