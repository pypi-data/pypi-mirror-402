"""Tests for the test command."""

from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.test import (
    _configure_pytest,
    _is_pytest_configured,
    run_tests,
)


class TestRunTests:
    """Tests for the run_tests function."""

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_success(
        self,
        mock_console,
        mock_is_configured,
        mock_activate,
        mock_run_env,
        mock_subprocess,
    ):
        """Test successful test execution."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run_env.return_value = Mock(returncode=0)
        # Mock subprocess.run to simulate pytest being installed
        mock_subprocess.return_value = Mock(returncode=0)

        run_tests(mock_config)

        mock_run_env.assert_called_once()
        assert any(
            "passed" in str(call).lower() for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_failure(
        self,
        mock_console,
        mock_is_configured,
        mock_activate,
        mock_run_env,
        mock_subprocess,
    ):
        """Test test execution failure."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run_env.return_value = Mock(returncode=1)
        mock_subprocess.return_value = Mock(returncode=0)

        run_tests(mock_config)

        assert any(
            "failed" in str(call).lower() for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test._configure_pytest")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_not_configured(
        self,
        mock_console,
        mock_is_configured,
        mock_activate,
        mock_run,
        mock_configure,
        mock_subprocess,
    ):
        """Test running tests when pytest is not configured."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = False
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)
        # Simulate pytest not being installed
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "python")

        run_tests(mock_config)

        mock_configure.assert_called_once_with(mock_config)

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_with_coverage(
        self, mock_console, mock_is_configured, mock_activate, mock_run, mock_subprocess
    ):
        """Test running tests with coverage."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)
        mock_subprocess.return_value = Mock(returncode=0)

        run_tests(mock_config, run_all=True)

        call_args = mock_run.call_args[0][0]
        assert "--cov" in call_args

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_specific_tests(
        self, mock_console, mock_is_configured, mock_activate, mock_run, mock_subprocess
    ):
        """Test running specific tests."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(returncode=0)
        mock_subprocess.return_value = Mock(returncode=0)

        run_tests(mock_config, pytest_args=["tests/test_foo.py", "tests/test_bar.py"])

        call_args = mock_run.call_args[0][0]
        assert "tests/test_foo.py" in call_args
        assert "tests/test_bar.py" in call_args

    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_env_activation_failure(
        self, mock_console, mock_is_configured, mock_activate
    ):
        """Test running tests when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.side_effect = RuntimeError("Venv not found")

        run_tests(mock_config)

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.activate_environment")
    @patch("maestria.commands.test._is_pytest_configured")
    @patch("maestria.commands.test.console")
    def test_run_tests_exception(
        self, mock_console, mock_is_configured, mock_activate, mock_run, mock_subprocess
    ):
        """Test running tests with exception."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_is_configured.return_value = True
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_run.side_effect = Exception("Test error")

        run_tests(mock_config)

        assert any(
            "Error running tests" in str(call)
            for call in mock_console.print.call_args_list
        )


class TestIsPytestConfigured:
    """Tests for the _is_pytest_configured function."""

    def test_is_pytest_configured_in_dev_deps(self):
        """Test when pytest is in dev dependencies."""
        mock_config = Mock()
        mock_config.dev_dependencies = ["pytest>=7.0.0", "pytest-cov>=3.0.0"]
        mock_config.scripts = {}

        assert _is_pytest_configured(mock_config) is True

    def test_is_pytest_configured_in_scripts(self):
        """Test when pytest is in scripts."""
        mock_config = Mock()
        mock_config.dev_dependencies = []
        mock_config.scripts = {"test": "pytest"}

        assert _is_pytest_configured(mock_config) is True

    def test_is_pytest_not_configured(self):
        """Test when pytest is not configured."""
        mock_config = Mock()
        mock_config.dev_dependencies = []
        mock_config.scripts = {}

        assert _is_pytest_configured(mock_config) is False


class TestConfigurePytest:
    """Tests for the _configure_pytest function."""

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.console")
    @patch("os.unlink")
    def test_configure_pytest_success(
        self, mock_unlink, mock_console, mock_run_env, mock_subprocess
    ):
        """Test successful pytest configuration."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_run_env.return_value = Mock(returncode=0)
        mock_subprocess.return_value = Mock(returncode=0)

        _configure_pytest(mock_config)

        assert any(
            "Installed pytest" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.console")
    def test_configure_pytest_env_failure(self, mock_console, mock_subprocess):
        """Test pytest configuration when uv pip install fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "uv")

        _configure_pytest(mock_config)

        assert any(
            "Failed to install pytest" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.console")
    def test_configure_pytest_install_failure(self, mock_console, mock_subprocess):
        """Test pytest configuration when installation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"
        mock_subprocess.side_effect = Exception("Install failed")

        _configure_pytest(mock_config)

        assert any(
            "Failed to install pytest" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.test.subprocess.run")
    @patch("maestria.commands.test.run_in_environment")
    @patch("maestria.commands.test.console")
    @patch("os.unlink")
    def test_configure_pytest_pyproject_update_failure(
        self, mock_unlink, mock_console, mock_run_env, mock_subprocess
    ):
        """Test pytest configuration when pyproject.toml update fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = "/path/to/project/.venv"

        # subprocess.run succeeds (uv pip install pytest)
        mock_subprocess.return_value = Mock(returncode=0)
        # run_in_environment fails (pyproject.toml update)
        mock_run_env.side_effect = Exception("Update failed")

        _configure_pytest(mock_config)

        assert any(
            "Failed to update pyproject.toml" in str(call)
            for call in mock_console.print.call_args_list
        )
