"""Tests for the install command."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.install import (
    check_installed_packages,
    install_dependencies,
    parse_dependencies,
)


class TestParseDependencies:
    """Tests for the parse_dependencies function."""

    def test_parse_dependencies_no_dev(self):
        """Test parsing dependencies without dev dependencies."""
        mock_config = Mock()
        mock_config.dependencies = ["click>=8.0.0", "rich>=10.0.0"]
        mock_config.dev_dependencies = ["pytest>=7.0.0"]

        deps = parse_dependencies(mock_config, dev=False)

        assert "click>=8.0.0" in deps
        assert "rich>=10.0.0" in deps
        assert "pytest>=7.0.0" not in deps

    def test_parse_dependencies_with_dev(self):
        """Test parsing dependencies with dev dependencies."""
        mock_config = Mock()
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = ["pytest>=7.0.0", "black>=22.0.0"]

        deps = parse_dependencies(mock_config, dev=True)

        assert "click>=8.0.0" in deps
        assert "pytest>=7.0.0" in deps
        assert "black>=22.0.0" in deps


class TestCheckInstalledPackages:
    """Tests for the check_installed_packages function."""

    @patch("maestria.commands.install.subprocess.run")
    def test_check_installed_packages_success(self, mock_run):
        """Test successful package check."""
        mock_run.return_value = Mock(
            stdout='[{"name": "click", "version": "8.1.0"}, {"name": "rich", "version": "10.0.0"}]',
            returncode=0,
        )

        packages = check_installed_packages(Path("/path/to/project"))

        assert packages["click"] == "8.1.0"
        assert packages["rich"] == "10.0.0"

    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.console")
    def test_check_installed_packages_failure(self, mock_console, mock_run):
        """Test package check failure."""
        mock_run.side_effect = Exception("Failed")

        packages = check_installed_packages(Path("/path/to/project"))

        assert packages == {}

    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.console")
    def test_check_installed_packages_verbose(self, mock_console, mock_run):
        """Test package check in verbose mode."""
        mock_run.return_value = Mock(stdout="[]", returncode=0)

        check_installed_packages(Path("/path/to/project"), verbose=True)

        mock_run.assert_called_once()


class TestInstallDependencies:
    """Tests for the install_dependencies function."""

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_success(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test successful dependency installation."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0", "rich>=10.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_check.side_effect = [{}, {"click": "8.1.0", "rich": "10.0.0"}]

        result = install_dependencies(mock_config)

        assert result is True
        assert any(
            "installed successfully" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_env_activation_failure(
        self, mock_console, mock_activate
    ):
        """Test dependency installation when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.side_effect = RuntimeError("Venv not found")

        result = install_dependencies(mock_config)

        assert result is False

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_no_deps_no_editable(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation with no dependencies and editable disabled."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = []
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_check.return_value = {}

        result = install_dependencies(mock_config, editable=False)

        assert result is True

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_with_dev(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation with dev dependencies."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = ["pytest>=7.0.0"]
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_check.side_effect = [{}, {"click": "8.1.0", "pytest": "7.1.0"}]

        result = install_dependencies(mock_config, dev=True)

        assert result is True

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_update_mode(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation in update mode."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_check.side_effect = [{"click": "8.0.0"}, {"click": "8.1.0"}]

        result = install_dependencies(mock_config, update=True)

        assert result is True
        call_args = mock_subprocess.call_args_list
        upgrade_calls = [call for call in call_args if "--upgrade" in str(call)]
        assert len(upgrade_calls) > 0

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_already_installed(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation when packages are already installed."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_check.return_value = {"click": "8.1.0"}

        result = install_dependencies(mock_config)

        assert result is True
        assert any(
            "already installed" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_editable_failure(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation when editable install fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_check.side_effect = [{}, {"click": "8.1.0"}]

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "--editable" in cmd:
                raise subprocess.CalledProcessError(1, "uv")
            return Mock(returncode=0)

        mock_subprocess.side_effect = run_side_effect

        result = install_dependencies(mock_config)

        assert result is True

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_install_failure(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation when installation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["click>=8.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_check.return_value = {}

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "click" in str(cmd):
                raise subprocess.CalledProcessError(1, "uv")
            return Mock(returncode=0)

        mock_subprocess.side_effect = run_side_effect

        result = install_dependencies(mock_config)

        assert result is False

    @patch("maestria.commands.install.check_installed_packages")
    @patch("maestria.commands.install.subprocess.run")
    @patch("maestria.commands.install.activate_environment")
    @patch("maestria.commands.install.console")
    def test_install_dependencies_case_insensitive(
        self, mock_console, mock_activate, mock_subprocess, mock_check
    ):
        """Test dependency installation with case-insensitive package names."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_config.venv_path = Path("/path/to/project/.venv")
        mock_config.dependencies = ["Click>=8.0.0"]
        mock_config.dev_dependencies = []
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_subprocess.return_value = Mock(returncode=0)
        mock_check.return_value = {"click": "8.1.0"}

        result = install_dependencies(mock_config)

        assert result is True
