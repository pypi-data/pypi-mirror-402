"""Tests for plugin management commands."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.plugin import (
    create_plugin,
    list_plugins,
)


class TestListPlugins:
    """Tests for list_plugins function."""

    @patch("maestria.plugins.discover_plugins")
    @patch("maestria.commands.plugin.console")
    def test_list_plugins_no_plugins(self, mock_console, mock_discover):
        """Test listing plugins when none installed."""
        mock_discover.return_value = {}
        config = Mock()

        list_plugins(config)

        mock_console.print.assert_called()
        assert any(
            "No Maestria plugins installed" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.plugins.discover_plugins")
    @patch("maestria.commands.plugin.console")
    def test_list_plugins_with_plugins(self, mock_console, mock_discover):
        """Test listing installed plugins."""
        from maestria.plugins import MaestriaPlugin

        class TestPlugin(MaestriaPlugin):
            name = "test-plugin"
            description = "A test plugin"

        class AnotherPlugin(MaestriaPlugin):
            name = "another-plugin"
            description = "Another test plugin"

        mock_discover.return_value = {
            "test-plugin": TestPlugin,
            "another-plugin": AnotherPlugin,
        }
        config = Mock()

        list_plugins(config)

        mock_console.print.assert_called()


class TestCreatePlugin:
    """Tests for create_plugin function."""

    def _create_mock_template(self, base_path):
        """Helper to create a mock plugin template."""
        template_path = base_path / "maestria" / "templates" / "data" / "plugin_template"
        os.makedirs(template_path / "src", exist_ok=True)
        (template_path / "README.md").write_text("# {{plugin_name}}")
        (template_path / "pyproject.toml").write_text(
            "[project]\nname = '{{plugin_name}}'"
        )
        return template_path

    @patch("maestria.templates.process_template_files")
    @patch("maestria.commands.plugin.console")
    @patch("maestria.commands.plugin.Path")
    def test_create_plugin_basic(self, mock_path_class, mock_console, mock_process):
        """Test creating a basic plugin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Setup mock Path to return our test template location
                template_dir = self._create_mock_template(Path(tmpdir))
                mock_file_path = Mock()
                mock_file_path.parent.parent = template_dir.parent.parent.parent
                mock_path_class.__file__ = str(mock_file_path)

                # Mock Path.cwd()
                mock_path_class.cwd.return_value = Path(tmpdir)

                create_plugin("my-plugin")

                plugin_dir = Path(tmpdir) / "maestria-my-plugin"
                assert plugin_dir.exists()
                mock_process.assert_called_once()

                # Verify context
                context = mock_process.call_args[0][1]
                assert context["plugin_name"] == "maestria-my-plugin"
                assert context["plugin_name_short"] == "my-plugin"
                assert context["package_name"] == "maestria_my_plugin"

            finally:
                os.chdir(original_cwd)

    @patch("maestria.templates.process_template_files")
    @patch("maestria.commands.plugin.console")
    @patch("maestria.commands.plugin.Path")
    def test_create_plugin_already_has_prefix(
        self, mock_path_class, mock_console, mock_process
    ):
        """Test creating plugin when name already has maestria prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                template_dir = self._create_mock_template(Path(tmpdir))
                mock_file_path = Mock()
                mock_file_path.parent.parent = template_dir.parent.parent.parent
                mock_path_class.__file__ = str(mock_file_path)
                mock_path_class.cwd.return_value = Path(tmpdir)

                create_plugin("maestria-test")

                plugin_dir = Path(tmpdir) / "maestria-test"
                assert plugin_dir.exists()

            finally:
                os.chdir(original_cwd)

    @patch("maestria.templates.process_template_files")
    @patch("maestria.commands.plugin.console")
    @patch("maestria.commands.plugin.Path")
    def test_create_plugin_directory_exists_continue(
        self, mock_path_class, mock_console, mock_process
    ):
        """Test creating plugin when directory exists and user confirms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create existing directory
                plugin_dir = Path(tmpdir) / "maestria-existing"
                plugin_dir.mkdir()

                # Mock user input to continue
                mock_console.input.return_value = "y"

                template_dir = self._create_mock_template(Path(tmpdir))
                mock_file_path = Mock()
                mock_file_path.parent.parent = template_dir.parent.parent.parent
                mock_path_class.__file__ = str(mock_file_path)
                mock_path_class.cwd.return_value = Path(tmpdir)

                create_plugin("existing")

                mock_console.input.assert_called_once()
                mock_process.assert_called_once()

            finally:
                os.chdir(original_cwd)

    @patch("maestria.commands.plugin.console")
    @patch("maestria.commands.plugin.Path")
    def test_create_plugin_directory_exists_cancel(self, mock_path_class, mock_console):
        """Test creating plugin when directory exists and user cancels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Create existing directory
                plugin_dir = Path(tmpdir) / "maestria-existing"
                plugin_dir.mkdir()

                # Mock user input to cancel
                mock_console.input.return_value = "n"

                mock_path_class.cwd.return_value = Path(tmpdir)

                create_plugin("existing")

                mock_console.input.assert_called_once()

            finally:
                os.chdir(original_cwd)

    @patch("maestria.templates.process_template_files")
    @patch("maestria.commands.plugin.console")
    @patch("maestria.commands.plugin.Path")
    def test_create_plugin_with_env_vars(
        self, mock_path_class, mock_console, mock_process
    ):
        """Test creating plugin uses safe hardcoded defaults (no env vars for security)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                template_dir = self._create_mock_template(Path(tmpdir))
                mock_file_path = Mock()
                mock_file_path.parent.parent = template_dir.parent.parent.parent
                mock_path_class.__file__ = str(mock_file_path)
                mock_path_class.cwd.return_value = Path(tmpdir)

                create_plugin("test")

                context = mock_process.call_args[0][1]
                # Verify safe defaults are used instead of environment variables
                assert context["author_name"] == "Your Name"
                assert context["author_email"] == ""

            finally:
                os.chdir(original_cwd)
