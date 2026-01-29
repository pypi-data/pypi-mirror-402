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

"""Package installation utilities for Maestria."""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from maestria.utils import get_venv_python

logger = logging.getLogger(__name__)


def install_dependencies(
    project_dir: Path,
    venv_path: Path,
    dependencies: List[str] = None,
    dev: bool = False,
    update: bool = False,
    verbose: bool = False,
) -> bool:
    """Install project dependencies.

    Args:
        project_dir: Path to project directory
        venv_path: Path to virtual environment
        dependencies: Specific dependencies to install (None = install from pyproject.toml)
        dev: Whether to install dev dependencies
        update: Whether to upgrade existing packages
        verbose: Whether to show verbose output

    Returns:
        True if installation succeeded, False otherwise
    """
    python_bin = get_venv_python(venv_path)

    if not python_bin.exists():
        logger.error(f"Python not found at {python_bin}")
        return False

    if verbose:
        logger.info(f"Using Python at {python_bin}")

    uv_available = shutil.which("uv") is not None

    if uv_available:
        if verbose:
            logger.info("UV found on system PATH, using it directly")

        cmd = ["uv", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
        if verbose:
            logger.info(f"→ Command: {' '.join(cmd)}")
            logger.info("→ Updating basic tools (pip, setuptools, wheel)")
        try:
            if verbose:
                subprocess.run(cmd, check=True)
            else:
                subprocess.run(
                    cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update basic tools: {e}")

        upgrade_flag = ["--upgrade"] if update else []
        if update and verbose:
            logger.info("Running in update mode...")

        if dependencies:
            if verbose:
                logger.info(
                    f"Installing specific dependencies: {', '.join(dependencies)}"
                )
            for dep in dependencies:
                cmd = ["uv", "pip", "install"] + upgrade_flag + [dep]
                if verbose:
                    logger.info(f"→ Command: {' '.join(cmd)}")
                    logger.info(f"→ Installing: {dep}")
                try:
                    if verbose:
                        subprocess.run(cmd, check=True)
                    else:
                        subprocess.run(
                            cmd,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {dep}: {e}")
                    return False
        else:
            target = ".[dev]" if dev else "."
            cmd = ["uv", "pip", "install", "-e", target] + upgrade_flag
            if verbose:
                logger.info(
                    f"Installing {'dev ' if dev else ''}dependencies with uv..."
                )
                logger.info(f"→ Command: {' '.join(cmd)}")
                logger.info(f"→ Working directory: {project_dir}")
                logger.info(
                    f"→ Installing project {'with dev extras' if dev else 'in editable mode'}"
                )
            try:
                if verbose:
                    subprocess.run(cmd, cwd=project_dir, check=True)
                else:
                    subprocess.run(
                        cmd,
                        cwd=project_dir,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {e}")
                return False
    else:
        logger.error("UV not found on system PATH")
        return False

    if verbose:
        logger.info("Dependencies installation completed successfully")
    return True


def main():
    """CLI entry point for dependency installation."""
    import argparse

    parser = argparse.ArgumentParser(description="Install project dependencies")
    parser.add_argument("--dev", action="store_true", help="Install dev dependencies")
    args = parser.parse_args()

    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"
    update = os.environ.get("MAESTRIA_UPDATE") == "1"

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(message)s"
    )

    venv_path = Path(os.environ.get("VENV_PATH", ".venv"))
    project_dir = Path.cwd()

    success = install_dependencies(
        project_dir=project_dir,
        venv_path=venv_path,
        dev=args.dev,
        update=update,
        verbose=verbose,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
