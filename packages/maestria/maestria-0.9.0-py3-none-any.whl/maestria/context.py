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

"""Global context for Maestria commands."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MaestriaContext(BaseModel):
    """Global context for Maestria commands.

    This class encapsulates the global configuration that all Maestria commands need,
    including the project directory and virtual environment path.

    Attributes:
        project_dir: The project directory (defaults to current working directory)
        venv_path: The virtual environment path (defaults to .venv in project_dir)
        verbose: Whether to enable verbose output
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_dir: Path = Field(default_factory=lambda: Path.cwd().resolve())
    venv_path: Optional[Path] = None
    verbose: bool = False

    def __init__(self, **data):
        """Initialize the context.

        If venv_path is not provided, it defaults to .venv in the project_dir.
        """
        super().__init__(**data)

        # Resolve project_dir to absolute path
        if not self.project_dir.is_absolute():
            self.project_dir = self.project_dir.resolve()

        # Set default venv_path if not provided
        if self.venv_path is None:
            self.venv_path = self.project_dir / ".venv"
        # If venv_path is relative, make it relative to project_dir
        elif not self.venv_path.is_absolute():
            self.venv_path = self.project_dir / self.venv_path

    @property
    def pyproject_path(self) -> Optional[Path]:
        """Get the path to pyproject.toml if it exists in the project directory."""
        pyproject = self.project_dir / "pyproject.toml"
        return pyproject if pyproject.exists() else None
