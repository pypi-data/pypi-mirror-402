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

"""Version management utilities for Maestria."""

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_version_from_pyproject(project_dir: Path) -> Optional[str]:
    """Extract version from pyproject.toml.

    Args:
        project_dir: Path to project directory

    Returns:
        Version string or None if not found
    """
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        logger.error(f"pyproject.toml not found at {pyproject_path}")
        return None

    try:
        import tomli  # type: ignore[import]
    except ImportError:
        try:
            import tomllib as tomli  # type: ignore[import,no-redef]
        except ImportError:
            logger.error("tomli or tomllib module not found")
            return None

    try:
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        version = data.get("project", {}).get("version")
        if version:
            logger.debug(f"Found version: {version}")
            return version
        else:
            logger.error("version not found in pyproject.toml")
            return None
    except Exception as e:
        logger.error(f"Error reading pyproject.toml: {str(e)}")
        return None


def main():
    """CLI entry point for version extraction."""
    logging.basicConfig(level=logging.ERROR, format="%(message)s")

    version = get_version_from_pyproject(Path.cwd())
    if version:
        print(version)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
