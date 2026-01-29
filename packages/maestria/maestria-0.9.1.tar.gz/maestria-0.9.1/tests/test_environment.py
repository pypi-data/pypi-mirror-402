"""Tests for the environment module."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from maestria.environment import (
    activate_environment,
    run_in_environment,
)


class TestActivateEnvironment:
    """Tests for the activate_environment function."""

    @patch("maestria.commands.env.subprocess.run")
    @patch("pathlib.Path.exists")
    @patch("maestria.environment.console")
    def test_activate_environment_success(self, mock_console, mock_exists, mock_run):
        """Test successful environment activation."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = activate_environment("/path/to/project")

        assert "venv_path" in result
        assert "python_path" in result
        assert "env_variables" in result

    @patch("pathlib.Path.exists")
    @patch("maestria.environment.console")
    def test_activate_environment_no_venv(self, mock_console, mock_exists):
        """Test environment activation when venv doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(RuntimeError, match="Virtual environment not found"):
            activate_environment("/path/to/project")

    @patch("maestria.environment.console")
    def test_activate_environment_invalid_structure(self, mock_console):
        """Test environment activation with invalid venv structure."""
        with patch("pathlib.Path.exists") as mock_exists:
            # Venv exists but bin/Scripts directory doesn't
            mock_exists.side_effect = [True, False]

            with pytest.raises(
                RuntimeError, match="Invalid virtual environment structure"
            ):
                activate_environment("/path/to/project")

    @patch("maestria.environment.console")
    def test_activate_environment_no_python(self, mock_console):
        """Test environment activation when Python executable is missing."""
        with patch("pathlib.Path.exists") as mock_exists:
            # Venv and bin dir exist but python executable doesn't
            mock_exists.side_effect = [True, True, False]

            with pytest.raises(RuntimeError, match="Python executable not found"):
                activate_environment("/path/to/project")

    @patch("pathlib.Path.exists")
    @patch("maestria.environment.console")
    def test_activate_environment_windows_paths(self, mock_console, mock_exists):
        """Test environment activation with correct path setup."""
        mock_exists.return_value = True

        result = activate_environment("/path/to/project")

        assert "venv_path" in result
        assert "python_path" in result
        assert "env_variables" in result
        assert "PATH" in result["env_variables"]

    @patch("pathlib.Path.exists")
    @patch("maestria.environment.console")
    def test_activate_environment_env_variables(self, mock_console, mock_exists):
        """Test environment activation sets correct environment variables."""
        mock_exists.return_value = True

        result = activate_environment("/path/to/project", verbose=True)

        assert "VIRTUAL_ENV" in result["env_variables"]
        assert str(result["venv_path"]) == result["env_variables"]["VIRTUAL_ENV"]

    @patch("maestria.environment.subprocess.run")
    @patch("pathlib.Path.exists")
    @patch("maestria.environment.platform.system")
    def test_activate_environment_windows(self, mock_platform, mock_exists, mock_run):
        """Test environment activation on Windows."""
        mock_platform.return_value = "Windows"
        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        result = activate_environment("C:\\path\\to\\project")

        assert "venv_path" in result
        assert "Scripts" in str(result["python_path"]) or "python" in str(
            result["python_path"]
        )


class TestRunInEnvironment:
    """Tests for the run_in_environment function."""

    @patch("maestria.environment.activate_environment")
    @patch("maestria.environment.subprocess.run")
    def test_run_in_environment_success(self, mock_run, mock_activate):
        """Test successful command execution in environment."""
        mock_activate.return_value = {
            "venv_path": Path("/path/.venv"),
            "python_path": Path("/path/.venv/bin/python"),
            "env_variables": {"PATH": "/path/.venv/bin:/usr/bin"},
        }
        mock_run.return_value = Mock(stdout="output", returncode=0)

        result = run_in_environment(["pytest"], "/path/to/project")

        assert result.stdout == "output"
        mock_run.assert_called_once()

    @patch("maestria.environment.activate_environment")
    @patch("maestria.environment.subprocess.run")
    def test_run_in_environment_failure(self, mock_run, mock_activate):
        """Test command execution failure in environment."""
        mock_activate.return_value = {
            "venv_path": Path("/path/.venv"),
            "python_path": Path("/path/.venv/bin/python"),
            "env_variables": {"PATH": "/path/.venv/bin:/usr/bin"},
        }
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")

        with pytest.raises(subprocess.CalledProcessError):
            run_in_environment(["pytest"], "/path/to/project")

    @patch("maestria.environment.activate_environment")
    def test_run_in_environment_activation_failure(self, mock_activate):
        """Test command execution when activation fails."""
        mock_activate.side_effect = RuntimeError("Venv not found")

        with pytest.raises(RuntimeError):
            run_in_environment(["pytest"], "/path/to/project")

    @patch("maestria.environment.activate_environment")
    @patch("maestria.environment.subprocess.run")
    @patch("maestria.environment.console")
    def test_run_in_environment_verbose(self, mock_console, mock_run, mock_activate):
        """Test command execution in verbose mode."""
        mock_activate.return_value = {
            "venv_path": Path("/path/.venv"),
            "python_path": Path("/path/.venv/bin/python"),
            "env_variables": {"PATH": "/path/.venv/bin:/usr/bin"},
        }
        mock_run.return_value = Mock(stdout="output", returncode=0)

        run_in_environment(["pytest"], "/path/to/project", verbose=True)

        assert mock_console.print.called

    @patch("maestria.environment.activate_environment")
    @patch("maestria.environment.subprocess.run")
    def test_run_in_environment_no_check(self, mock_run, mock_activate):
        """Test command execution without check."""
        mock_activate.return_value = {
            "venv_path": Path("/path/.venv"),
            "python_path": Path("/path/.venv/bin/python"),
            "env_variables": {"PATH": "/path/.venv/bin:/usr/bin"},
        }
        mock_run.return_value = Mock(stdout="output", returncode=1)

        result = run_in_environment(["pytest"], "/path/to/project", check=False)

        assert result.returncode == 1

    @patch("maestria.environment.activate_environment")
    @patch("maestria.environment.subprocess.run")
    def test_run_in_environment_no_capture(self, mock_run, mock_activate):
        """Test command execution without capturing output."""
        mock_activate.return_value = {
            "venv_path": Path("/path/.venv"),
            "python_path": Path("/path/.venv/bin/python"),
            "env_variables": {"PATH": "/path/.venv/bin:/usr/bin"},
        }
        mock_run.return_value = Mock(returncode=0)

        run_in_environment(["pytest"], "/path/to/project", capture_output=False)

        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is False
