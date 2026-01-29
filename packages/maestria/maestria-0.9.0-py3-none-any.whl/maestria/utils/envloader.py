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

"""Environment loading and validation utilities for Maestria."""

import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from maestria.security import SecurityError, validate_executable, validate_path
from maestria.utils import get_venv_python, normalize_venv_path

logger = logging.getLogger(__name__)


def load_and_validate_env(
    project_dir: Path, venv_path: Path, verbose: bool = False
) -> bool:
    """Load and validate the virtual environment.

    Args:
        project_dir: Path to the project directory
        venv_path: Path to the virtual environment (relative or absolute)
        verbose: Whether to show verbose output

    Returns:
        True if environment is valid, False otherwise
    """
    # Validate project_dir
    try:
        project_dir = validate_path(project_dir, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        logger.error(f"Invalid project directory: {e}")
        return False

    # Make venv_path absolute relative to project_dir if needed
    venv_path = normalize_venv_path(project_dir, venv_path)

    # Validate venv_path
    try:
        venv_path = validate_path(venv_path, allow_absolute=True, must_exist=True)
    except SecurityError as e:
        logger.error(f"Virtual environment not found: {e}")
        logger.info("Please run 'maestria env setup' to create it")
        return False

    python_bin = get_venv_python(venv_path)

    # Check if python executable exists first
    if not python_bin.exists():
        logger.error("Python executable not found in virtual environment")
        return False

    # Validate python executable
    try:
        is_windows = platform.system() == "Windows"
        venv_bin_path = venv_path / ("Scripts" if is_windows else "bin")
        python_bin = validate_executable(python_bin, allowed_dirs=[venv_bin_path])
    except SecurityError as e:
        logger.error(f"Python executable validation failed: {e}")
        return False

    if verbose:
        logger.info(f"→ Using Python at: {python_bin}")
        logger.info(f"→ Virtual environment at: {venv_path}")

    # Allowlist of safe dependency names (prevent injection via pkg names)
    safe_key_deps = ["rich", "click", "tomli", "tomli_w"]
    key_deps = safe_key_deps
    missing_deps = []

    for pkg in key_deps:
        # Validate package name is safe (alphanumeric, dash, underscore only)
        if not all(c.isalnum() or c in ("-", "_") for c in pkg):
            logger.error(f"Invalid package name: {pkg}")
            continue

        module_name = pkg.replace("-", "_")

        try:
            subprocess.run(
                [str(python_bin), "-c", f"import {module_name}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError:
            missing_deps.append(pkg)

    if missing_deps:
        if verbose:
            logger.info(f"→ Missing dependencies: {', '.join(missing_deps)}")

        if shutil.which("uv"):
            cmd = ["uv", "pip", "install"] + missing_deps
            if verbose:
                logger.info("→ Installing with uv pip")
                logger.info(f"→ Command: {' '.join(cmd)}")
        else:
            cmd = [str(python_bin), "-m", "pip", "install"] + missing_deps
            if verbose:
                logger.info("→ Installing with pip")
                logger.info(f"→ Command: {' '.join(cmd)}")

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")

        still_missing = []
        for pkg in missing_deps:
            module_name = pkg.replace("-", "_")
            try:
                subprocess.run(
                    [str(python_bin), "-c", f"import {module_name}"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError:
                still_missing.append(pkg)

        if still_missing:
            logger.error(
                f"Failed to install required dependencies: {', '.join(still_missing)}"
            )
            return False

    if verbose:
        logger.info("→ Environment loaded and validated successfully")
    return True


def main():
    """CLI entry point for environment loading."""
    import os

    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(message)s"
    )

    project_dir = Path.cwd()
    # Use default .venv path - no need for environment variable
    venv_path = Path(".venv")

    if load_and_validate_env(project_dir, venv_path, verbose):
        print("Environment ready")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
