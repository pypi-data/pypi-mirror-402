"""Tests for the build command."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.build import build_project


class TestBuildProject:
    """Tests for the build_project function."""

    @patch("maestria.commands.build.run_in_environment")
    @patch("maestria.commands.build.activate_environment")
    @patch("maestria.commands.build.console")
    def test_build_project_success(self, mock_console, mock_activate, mock_run):
        """Test successful project build."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(
            stdout="Successfully built dist/package-0.1.0.tar.gz\nSuccessfully built dist/package-0.1.0-py3-none-any.whl",
            returncode=0,
        )

        build_project(mock_config)

        assert any(
            "built successfully" in str(call).lower()
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.build.activate_environment")
    @patch("maestria.commands.build.console")
    def test_build_project_env_activation_failure(self, mock_console, mock_activate):
        """Test project build when environment activation fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.side_effect = RuntimeError("Venv not found")

        build_project(mock_config)

        assert any("Error" in str(call) for call in mock_console.print.call_args_list)

    @patch("maestria.commands.build.run_in_environment")
    @patch("maestria.commands.build.activate_environment")
    @patch("maestria.commands.build.console")
    def test_build_project_build_failure(self, mock_console, mock_activate, mock_run):
        """Test project build when build fails."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "build", stderr="Build error"
        )

        build_project(mock_config)

        assert any(
            "Failed to build project" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.commands.build.run_in_environment")
    @patch("maestria.commands.build.activate_environment")
    @patch("maestria.commands.build.console")
    def test_build_project_with_output_files(
        self, mock_console, mock_activate, mock_run
    ):
        """Test project build with output files listed."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(
            stdout="dist/mypackage-1.0.0.tar.gz\ndist/mypackage-1.0.0-py3-none-any.whl",
            returncode=0,
        )

        build_project(mock_config)

        assert any(
            "Built packages" in str(call) for call in mock_console.print.call_args_list
        )

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.commands.build.run_in_environment")
    @patch("maestria.commands.build.activate_environment")
    @patch("maestria.commands.build.console")
    def test_build_project_verbose(self, mock_console, mock_activate, mock_run):
        """Test project build in verbose mode."""
        mock_config = Mock()
        mock_config.root_dir = "/path/to/project"
        mock_activate.return_value = {"python_path": Path("/venv/bin/python")}
        mock_run.return_value = Mock(stdout="", returncode=0)

        build_project(mock_config)

        mock_run.assert_called_once()
