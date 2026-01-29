"""Tests for the env command."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from maestria.commands.env import (
    is_module_installed,
    run_with_venv_activation,
    setup_environment,
    show_environment_info,
    update_environment,
)


class TestIsModuleInstalled:
    """Tests for the is_module_installed function."""

    @patch("maestria.commands.env.importlib.util.find_spec")
    def test_is_module_installed_true(self, mock_find_spec):
        """Test when module is installed."""
        mock_find_spec.return_value = Mock()
        assert is_module_installed("pytest") is True

    @patch("maestria.commands.env.importlib.util.find_spec")
    def test_is_module_installed_false(self, mock_find_spec):
        """Test when module is not installed."""
        mock_find_spec.return_value = None
        assert is_module_installed("nonexistent_module") is False


class TestRunWithVenvActivation:
    """Tests for the run_with_venv_activation function."""

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.platform.system")
    def test_run_with_venv_activation_unix(self, mock_platform, mock_run):
        """Test running command with venv activation on Unix."""
        mock_platform.return_value = "Linux"
        mock_run.return_value = Mock(stdout="output", returncode=0)

        result = run_with_venv_activation(
            ["python", "-m", "pytest"],
            "/path/to/venv",
            "/path/to/project",
        )

        assert result.stdout == "output"
        call_env = mock_run.call_args[1]["env"]
        assert "/path/to/venv/bin" in call_env["PATH"]
        assert call_env["VIRTUAL_ENV"] == "/path/to/venv"

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.platform.system")
    def test_run_with_venv_activation_windows(self, mock_platform, mock_run):
        """Test running command with venv activation on Windows."""
        mock_platform.return_value = "Windows"
        mock_run.return_value = Mock(stdout="output", stderr="", returncode=0)

        run_with_venv_activation(
            ["python", "-m", "pytest"],
            r"C:\path\to\venv",
            r"C:\path\to\project",
        )

        call_env = mock_run.call_args[1]["env"]
        # Windows uses forward slash in the path due to os.path.join behavior
        assert (
            "C:" in call_env["PATH"]
            and "venv" in call_env["PATH"]
            and "Scripts" in call_env["PATH"]
        )

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.platform.system")
    @patch("maestria.commands.env.console")
    def test_run_with_venv_activation_verbose(
        self, mock_console, mock_platform, mock_run
    ):
        """Test running command with venv activation in verbose mode."""
        mock_platform.return_value = "Linux"
        mock_run.return_value = Mock(stdout="test output", returncode=0)

        run_with_venv_activation(
            ["python", "-m", "pytest"],
            "/path/to/venv",
            "/path/to/project",
        )

        assert mock_console.print.called

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.platform.system")
    def test_run_with_venv_activation_custom_env(self, mock_platform, mock_run):
        """Test running command with custom environment variables."""
        mock_platform.return_value = "Linux"
        mock_run.return_value = Mock(stdout="output", returncode=0)

        custom_env = {"CUSTOM_VAR": "custom_value"}
        run_with_venv_activation(
            ["python", "-m", "pytest"],
            "/path/to/venv",
            "/path/to/project",
            env=custom_env,
        )

        call_env = mock_run.call_args[1]["env"]
        assert call_env["CUSTOM_VAR"] == "custom_value"

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.platform.system")
    @patch("maestria.commands.env.console")
    def test_run_with_venv_activation_failure(
        self, mock_console, mock_platform, mock_run
    ):
        """Test running command with venv activation that fails."""
        mock_platform.return_value = "Linux"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "python", stderr="error"
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_with_venv_activation(
                ["python", "-m", "pytest"],
                "/path/to/venv",
                "/path/to/project",
            )


class TestSetupEnvironment:
    """Tests for the setup_environment function."""

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("maestria.commands.env.os.chmod")
    def test_setup_environment_success(self, mock_chmod, mock_console, mock_run):
        """Test successful environment setup."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with patch("pathlib.Path.exists", return_value=True):
            setup_environment(mock_config)

        assert mock_console.print.called

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    def test_setup_environment_uv_not_found(self, mock_console, mock_run):
        """Test environment setup when UV is not found."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "uv" and cmd[1] == "venv":
                raise FileNotFoundError()
            return Mock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = run_side_effect

        setup_environment(mock_config)

        assert any(
            "UV not found" in str(call) for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    def test_setup_environment_venv_creation_failure(self, mock_console, mock_run):
        """Test environment setup when venv creation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run.side_effect = subprocess.CalledProcessError(1, "uv", stderr="error")

        setup_environment(mock_config)

        assert any(
            "Failed to create virtual environment" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("maestria.commands.env.platform.system")
    def test_setup_environment_windows(self, mock_platform, mock_console, mock_run):
        """Test environment setup on Windows."""
        mock_platform.return_value = "Windows"
        mock_config = Mock()
        mock_config.root_dir = "C:\\path\\to\\project"
        mock_config.venv_path = "C:\\path\\to\\project\\.venv"
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with patch("pathlib.Path.exists", return_value=True):
            setup_environment(mock_config)

        assert mock_console.print.called

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("maestria.commands.env.os.chmod")
    def test_setup_environment_verbose(self, mock_chmod, mock_console, mock_run):
        """Test environment setup in verbose mode."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        with patch("pathlib.Path.exists", return_value=True):
            setup_environment(mock_config)

        assert mock_console.print.called


class TestUpdateEnvironment:
    """Tests for the update_environment function."""

    @patch("maestria.commands.env.setup_environment")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_update_environment_no_venv(self, mock_exists, mock_console, mock_setup):
        """Test updating environment when venv doesn't exist."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"

        update_environment(mock_config)

        # update_environment now just passes the config object
        mock_setup.assert_called_once_with(mock_config)

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    @patch("maestria.commands.env.platform.system")
    def test_update_environment_success(
        self, mock_platform, mock_exists, mock_console, mock_run
    ):
        """Test successful environment update."""
        mock_platform.return_value = "Linux"
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        update_environment(mock_config)

        assert any(
            "updated successfully" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    @patch("maestria.commands.env.platform.system")
    def test_update_environment_failure(
        self, mock_platform, mock_exists, mock_console, mock_run
    ):
        """Test environment update failure."""
        mock_platform.return_value = "Linux"
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "script", stderr="error"
        )

        update_environment(mock_config)

        assert any(
            "Failed to update dependencies" in str(call)
            for call in mock_console.print.call_args_list
        )


class TestShowEnvironmentInfo:
    """Tests for the show_environment_info function."""

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_no_venv(self, mock_exists, mock_console, mock_run):
        """Test showing environment info when venv doesn't exist."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = []
        mock_config.path = None
        mock_config.name = "test-project"
        mock_config.version = "1.0.0"
        mock_run.return_value = Mock(stdout="uv 0.1.0", returncode=0)

        show_environment_info(mock_config)

        assert mock_console.print.called

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_with_venv(self, mock_exists, mock_console, mock_run):
        """Test showing environment info with venv."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = ["click>=8.0.0", "rich>=10.0.0"]
        mock_config.dev_dependencies = []
        mock_config.path = Mock()
        mock_config.path.exists.return_value = True
        mock_config.name = "test"
        mock_config.version = "1.0.0"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "uv" and cmd[1] == "--version":
                return Mock(stdout="uv 0.1.0", returncode=0)
            elif cmd[0] == "uv" and cmd[1] == "pip" and cmd[2] == "list":
                return Mock(
                    stdout="Package Version\n------- -------\nclick 8.1.0\nrich 10.0.0",
                    returncode=0,
                )
            return Mock(stdout="Python 3.10.0", returncode=0)

        mock_run.side_effect = run_side_effect

        show_environment_info(mock_config)

        assert mock_console.print.called

    @patch.dict("os.environ", {"VIRTUAL_ENV": "/path/to/active/venv"})
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_active_venv(self, mock_exists, mock_console):
        """Test showing environment info with active venv."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = []
        mock_config.path = None
        mock_config.name = "test-project"
        mock_config.version = "1.0.0"

        show_environment_info(mock_config)

        assert mock_console.print.called

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_verbose(self, mock_exists, mock_console, mock_run):
        """Test showing environment info in verbose mode."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = []
        mock_config.dev_dependencies = []
        mock_config.path = Mock()
        mock_config.path.exists.return_value = True
        mock_config.name = "test-project"
        mock_config.version = "1.0.0"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "uv" and cmd[1] == "--version":
                return Mock(stdout="uv 0.1.0", returncode=0)
            elif cmd[0] == "uv" and cmd[1] == "pip" and cmd[2] == "list":
                return Mock(
                    stdout="Package Version\n------- -------\nclick 8.1.0\nrich 10.0.0\npytest 7.0.0",
                    returncode=0,
                )
            return Mock(stdout="Python 3.10.0", returncode=0)

        mock_run.side_effect = run_side_effect

        show_environment_info(mock_config)

        assert mock_console.print.called

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_uv_not_installed(
        self, mock_exists, mock_console, mock_run
    ):
        """Test showing environment info when UV is not installed."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = []
        mock_config.path = None
        mock_config.name = "test-project"
        mock_config.version = "1.0.0"

        mock_run.side_effect = FileNotFoundError()

        show_environment_info(mock_config)

        assert mock_console.print.called

    @patch("maestria.commands.env.subprocess.run")
    @patch("maestria.commands.env.console")
    @patch("pathlib.Path.exists")
    def test_show_environment_info_pip_list_failure(
        self, mock_exists, mock_console, mock_run
    ):
        """Test showing environment info when pip list fails."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_config.dependencies = []
        mock_config.dev_dependencies = []
        mock_config.path = Mock()
        mock_config.path.exists.return_value = True
        mock_config.name = "test-project"
        mock_config.version = "1.0.0"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "uv" and cmd[1] == "--version":
                return Mock(stdout="uv 0.1.0", returncode=0)
            elif cmd[0] == "uv" and cmd[1] == "pip" and cmd[2] == "list":
                raise subprocess.CalledProcessError(1, "uv")
            return Mock(stdout="", returncode=0)

        mock_run.side_effect = run_side_effect

        show_environment_info(mock_config)

        assert mock_console.print.called
