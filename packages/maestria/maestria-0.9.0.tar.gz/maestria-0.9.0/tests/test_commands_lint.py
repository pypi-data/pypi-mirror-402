"""Tests for the lint command."""

from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.lint import (
    _configure_linting,
    _is_linting_configured,
    run_linting,
)


class TestRunLinting:
    """Tests for the run_linting function."""

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    @patch("pathlib.Path.exists")
    def test_run_linting_success(
        self, mock_exists, mock_console, mock_is_configured, mock_activate, mock_run
    ):
        """Test successful linting."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_linting(mock_config)

        assert mock_run.call_count >= 2

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    @patch("pathlib.Path.exists")
    def test_run_linting_check_mode(
        self, mock_exists, mock_console, mock_is_configured, mock_activate, mock_run
    ):
        """Test linting in check mode."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_linting(mock_config, check=True)

        black_call = [call for call in mock_run.call_args_list if "black" in str(call)][
            0
        ]
        assert "--check" in str(black_call)

    @patch("maestria.commands.lint._configure_linting")
    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    @patch("pathlib.Path.exists")
    def test_run_linting_not_configured(
        self,
        mock_exists,
        mock_console,
        mock_is_configured,
        mock_activate,
        mock_run,
        mock_configure,
    ):
        """Test linting when tools are not configured."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = False
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        run_linting(mock_config)

        mock_configure.assert_called_once_with(mock_config)

    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    def test_run_linting_env_activation_failure(
        self, mock_console, mock_is_configured, mock_activate
    ):
        """Test linting when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.side_effect = RuntimeError("Venv not found")

        run_linting(mock_config)

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    @patch("pathlib.Path.exists")
    def test_run_linting_black_failure(
        self, mock_exists, mock_console, mock_is_configured, mock_activate, mock_run
    ):
        """Test linting when black fails."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "black" in cmd:
                return Mock(returncode=1)
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        run_linting(mock_config)

        assert any(
            "formatting issues" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    def test_run_linting_mypy_with_src_dir(
        self, mock_console, mock_is_configured, mock_activate, mock_run
    ):
        """Test linting with src directory."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            run_linting(mock_config)

        mypy_call = [call for call in mock_run.call_args_list if "mypy" in str(call)][0]
        assert "src" in str(mypy_call)

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint._is_linting_configured")
    @patch("maestria.commands.lint.console")
    @patch("pathlib.Path.exists")
    def test_run_linting_ruff_not_available(
        self, mock_exists, mock_console, mock_is_configured, mock_activate, mock_run
    ):
        """Test linting when ruff is not available."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "ruff" in cmd:
                raise Exception("ruff not found")
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        run_linting(mock_config)

        assert any(
            "skipping" in str(call).lower()
            for call in mock_console.print.call_args_list
        )


class TestIsLintingConfigured:
    """Tests for the _is_linting_configured function."""

    def test_is_linting_configured_with_black(self):
        """Test when black is in dev dependencies."""
        mock_config = Mock()
        mock_config.dev_dependencies = ["black>=22.0.0"]
        mock_config.scripts = {}

        assert _is_linting_configured(mock_config) is True

    def test_is_linting_configured_with_mypy(self):
        """Test when mypy is in dev dependencies."""
        mock_config = Mock()
        mock_config.dev_dependencies = ["mypy>=0.991"]
        mock_config.scripts = {}

        assert _is_linting_configured(mock_config) is True

    def test_is_linting_configured_with_ruff(self):
        """Test when ruff is in dev dependencies."""
        mock_config = Mock()
        mock_config.dev_dependencies = ["ruff>=0.1.0"]
        mock_config.scripts = {}

        assert _is_linting_configured(mock_config) is True

    def test_is_linting_configured_with_script(self):
        """Test when lint script exists."""
        mock_config = Mock()
        mock_config.dev_dependencies = []
        mock_config.scripts = {"lint": "black . && mypy ."}

        assert _is_linting_configured(mock_config) is True

    def test_is_linting_not_configured(self):
        """Test when linting is not configured."""
        mock_config = Mock()
        mock_config.dev_dependencies = []
        mock_config.scripts = {}

        assert _is_linting_configured(mock_config) is False


class TestConfigureLinting:
    """Tests for the _configure_linting function."""

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint.console")
    @patch("os.unlink")
    def test_configure_linting_success(
        self, mock_unlink, mock_console, mock_activate, mock_run
    ):
        """Test successful linting configuration."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)

        _configure_linting(mock_config)

        assert any(
            "Installed black, mypy, and ruff" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint.console")
    def test_configure_linting_env_failure(self, mock_console, mock_activate):
        """Test linting configuration when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_activate.side_effect = RuntimeError("Venv not found")

        _configure_linting(mock_config)

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint.console")
    def test_configure_linting_install_failure(
        self, mock_console, mock_activate, mock_run
    ):
        """Test linting configuration when installation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.side_effect = Exception("Install failed")

        _configure_linting(mock_config)

        assert any(
            "Failed to install linting tools" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.lint.run_in_environment")
    @patch("maestria.commands.lint.activate_environment")
    @patch("maestria.commands.lint.console")
    @patch("os.unlink")
    def test_configure_linting_pyproject_update_failure(
        self, mock_unlink, mock_console, mock_activate, mock_run
    ):
        """Test linting configuration when pyproject.toml update fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if str(cmd[0]).endswith("python") and len(cmd) == 5:
                return Mock(returncode=0)
            elif str(cmd[0]).endswith("python") and len(cmd) == 2:
                raise Exception("Update failed")
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        _configure_linting(mock_config)

        mock_run.assert_called()
