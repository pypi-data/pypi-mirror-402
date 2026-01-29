"""Tests for utils helper functions."""

from pathlib import Path
from unittest.mock import patch

from maestria.utils import (
    get_venv_bin_dir,
    get_venv_executable,
    get_venv_python,
    normalize_venv_path,
)


class TestGetVenvBinDir:
    """Tests for get_venv_bin_dir function."""

    def test_unix_path(self):
        """Test bin directory on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/path/to/venv")
            result = get_venv_bin_dir(venv_path)
            assert result == Path("/path/to/venv/bin")

    def test_windows_path(self):
        """Test Scripts directory on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/path/to/venv")
            result = get_venv_bin_dir(venv_path)
            assert result == Path("C:/path/to/venv/Scripts")


class TestGetVenvPython:
    """Tests for get_venv_python function."""

    def test_unix_python(self):
        """Test Python executable on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/path/to/venv")
            result = get_venv_python(venv_path)
            assert result == Path("/path/to/venv/bin/python")

    def test_windows_python(self):
        """Test Python executable on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/path/to/venv")
            result = get_venv_python(venv_path)
            assert result == Path("C:/path/to/venv/Scripts/python.exe")


class TestGetVenvExecutable:
    """Tests for get_venv_executable function."""

    def test_unix_no_extension(self):
        """Test executable without extension on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/path/to/venv")
            result = get_venv_executable(venv_path, "pytest")
            assert result == Path("/path/to/venv/bin/pytest")

    def test_unix_with_extension_ignored(self):
        """Test that Windows extension is ignored on Unix."""
        with patch("sys.platform", "linux"):
            venv_path = Path("/path/to/venv")
            result = get_venv_executable(venv_path, "pytest", ".exe")
            assert result == Path("/path/to/venv/bin/pytest")

    def test_windows_no_extension(self):
        """Test executable without extension on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/path/to/venv")
            result = get_venv_executable(venv_path, "pytest", None)
            assert result == Path("C:/path/to/venv/Scripts/pytest")

    def test_windows_with_extension(self):
        """Test executable with extension on Windows."""
        with patch("sys.platform", "win32"):
            venv_path = Path("C:/path/to/venv")
            result = get_venv_executable(venv_path, "pytest", ".exe")
            assert result == Path("C:/path/to/venv/Scripts/pytest.exe")


class TestNormalizeVenvPath:
    """Tests for normalize_venv_path function."""

    def test_relative_path(self):
        """Test normalizing relative path."""
        project_dir = Path("/project")
        venv_path = Path(".venv")
        result = normalize_venv_path(project_dir, venv_path)
        assert result == Path("/project/.venv")

    def test_absolute_path_unchanged(self):
        """Test that absolute path is unchanged."""
        project_dir = Path("/project")
        venv_path = Path("/absolute/venv")
        result = normalize_venv_path(project_dir, venv_path)
        assert result == Path("/absolute/venv")

    def test_nested_relative_path(self):
        """Test normalizing nested relative path."""
        project_dir = Path("/project")
        venv_path = Path("envs/.venv")
        result = normalize_venv_path(project_dir, venv_path)
        assert result == Path("/project/envs/.venv")

    def test_with_tmp_path(self, tmp_path):
        """Test with real temporary directory."""
        venv_path = Path(".venv")
        result = normalize_venv_path(tmp_path, venv_path)
        assert result == tmp_path / ".venv"
        assert result.is_absolute()
