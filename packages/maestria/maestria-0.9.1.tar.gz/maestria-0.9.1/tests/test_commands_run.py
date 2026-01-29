"""Tests for the run command."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.run import run_script


class TestRunScript:
    """Tests for the run_script function."""

    @patch("maestria.commands.run.run_in_environment")
    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    def test_run_script_success(self, mock_console, mock_activate, mock_run):
        """Test successful script execution."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": "python -m myapp"}
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_script(mock_config, "dev")

        mock_run.assert_called_once()

    @patch("maestria.commands.run.console")
    def test_run_script_not_found(self, mock_console):
        """Test running a script that doesn't exist."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": "python -m myapp"}

        run_script(mock_config, "nonexistent")

        assert any(
            "not found" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.run.console")
    def test_run_script_no_scripts(self, mock_console):
        """Test running script when no scripts are defined."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = None

        run_script(mock_config, "dev")

        assert any(
            "No scripts defined" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.run.run_in_environment")
    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    def test_run_script_with_args(self, mock_console, mock_activate, mock_run):
        """Test script execution with additional arguments."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": "python -m myapp"}
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_script(mock_config, "dev", args=["--port", "8000"])

        call_args = mock_run.call_args[0][0]
        assert "--port" in call_args
        assert "8000" in call_args

    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    def test_run_script_env_activation_failure(self, mock_console, mock_activate):
        """Test script execution when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": "python -m myapp"}
        mock_activate.side_effect = RuntimeError("Venv not found")

        run_script(mock_config, "dev")

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)

    @patch("maestria.commands.run.run_in_environment")
    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    def test_run_script_execution_failure(self, mock_console, mock_activate, mock_run):
        """Test script execution when script fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": "python -m myapp"}
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.side_effect = subprocess.CalledProcessError(1, "python")

        run_script(mock_config, "dev")

        assert any(
            "Error running script" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.run.run_in_environment")
    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    @patch("os.path.exists")
    def test_run_script_with_venv_command(
        self, mock_exists, mock_console, mock_activate, mock_run
    ):
        """Test script execution with command from venv."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"lint": "black ."}
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_script(mock_config, "lint")

        mock_run.assert_called_once()

    @patch("maestria.commands.run.run_in_environment")
    @patch("maestria.commands.run.activate_environment")
    @patch("maestria.commands.run.console")
    def test_run_script_python_command(self, mock_console, mock_activate, mock_run):
        """Test script execution with python command."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"start": "python app.py"}
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_script(mock_config, "start")

        call_args = mock_run.call_args[0][0]
        assert str(call_args[0]).endswith("python")
        assert "app.py" in call_args

    @patch("maestria.commands.run.console")
    def test_run_script_dict_format(self, mock_console):
        """Test script execution with dict format."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.scripts = {"dev": {"cmd": "python -m myapp"}}

        run_script(mock_config, "nonexistent")

        assert any(
            "dev: python -m myapp" in str(call)
            for call in mock_console.print.call_args_list
        )
