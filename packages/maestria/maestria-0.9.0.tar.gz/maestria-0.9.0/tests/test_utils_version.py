"""Tests for version utilities."""

import os

import pytest

from maestria.utils.version import get_version_from_pyproject, main


class TestGetVersionFromPyproject:
    """Tests for get_version_from_pyproject function."""

    def test_get_version_success(self, tmp_path):
        """Test successful version extraction."""
        pyproject_content = b"""
[project]
name = "test-project"
version = "1.2.3"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        version = get_version_from_pyproject(tmp_path)

        assert version == "1.2.3"

    def test_get_version_missing_file(self, tmp_path):
        """Test when pyproject.toml doesn't exist."""
        version = get_version_from_pyproject(tmp_path)

        assert version is None

    def test_get_version_no_version_field(self, tmp_path):
        """Test when version field is missing."""
        pyproject_content = b"""
[project]
name = "test-project"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        version = get_version_from_pyproject(tmp_path)

        assert version is None

    def test_get_version_invalid_toml(self, tmp_path):
        """Test with malformed TOML."""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("invalid toml content [[[")

        version = get_version_from_pyproject(tmp_path)

        assert version is None

    def test_get_version_custom_path(self, tmp_path):
        """Test with custom project directory."""
        subdir = tmp_path / "subproject"
        subdir.mkdir()
        pyproject_content = b"""
[project]
version = "0.5.0"
"""
        pyproject_path = subdir / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        version = get_version_from_pyproject(subdir)

        assert version == "0.5.0"

    def test_get_version_default_cwd(self, tmp_path):
        """Test with explicit Path.cwd() call (simulating main() behavior)."""
        pyproject_content = b"""
[project]
version = "2.0.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            from pathlib import Path

            version = get_version_from_pyproject(Path.cwd())
            assert version == "2.0.0"
        finally:
            os.chdir(orig_cwd)

    def test_get_version_no_project_section(self, tmp_path):
        """Test when project section is missing."""
        pyproject_content = b"""
[tool.other]
key = "value"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        version = get_version_from_pyproject(tmp_path)

        assert version is None


class TestMain:
    """Tests for CLI entry point."""

    def test_main_cli_success(self, tmp_path, capsys):
        """Test CLI with successful version extraction."""
        pyproject_content = b"""
[project]
version = "1.0.0"
"""
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(pyproject_content)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "1.0.0" in captured.out
        finally:
            os.chdir(orig_cwd)

    def test_main_cli_failure(self, tmp_path):
        """Test CLI when version not found."""
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(orig_cwd)

    def test_main_cli_missing_file(self, tmp_path):
        """Test CLI when pyproject.toml is missing."""
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(orig_cwd)
