"""Test configuration for {{project_name}}."""

import os
import sys
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir():
    """Return the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def add_project_to_path(project_root):
    """Add the project root to sys.path for imports.

    This is especially useful when running tests during development
    before the package is installed.
    """
    project_path = str(project_root)
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
