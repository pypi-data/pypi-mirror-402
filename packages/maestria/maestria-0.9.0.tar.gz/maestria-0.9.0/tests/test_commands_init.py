"""Tests for the init command."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from maestria.commands.init import (
    gather_project_info,
    init_git_repo,
    initialize_project,
    run_command,
)


class TestRunCommand:
    """Tests for the run_command function."""

    @patch("maestria.commands.init.subprocess.run")
    def test_run_command_list(self, mock_run):
        """Test running a command with a list."""
        mock_run.return_value = Mock(stdout="output", stderr="")
        result = run_command(["git", "status"])

        mock_run.assert_called_once()
        assert result.stdout == "output"

    @patch("maestria.commands.init.subprocess.run")
    def test_run_command_string(self, mock_run):
        """Test running a command with a string."""
        mock_run.return_value = Mock(stdout="output", stderr="")
        result = run_command("git status")

        mock_run.assert_called_once()
        assert result.stdout == "output"

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.commands.init.subprocess.run")
    @patch("maestria.commands.init.console")
    def test_run_command_verbose(self, mock_console, mock_run):
        """Test running a command in verbose mode."""
        mock_run.return_value = Mock(stdout="test output", stderr="")
        run_command(["git", "status"])

        assert mock_console.print.called

    @patch("maestria.commands.init.subprocess.run")
    def test_run_command_with_cwd(self, mock_run):
        """Test running a command with a custom working directory."""
        mock_run.return_value = Mock(stdout="", stderr="")
        test_path = Path("/test/path")

        run_command(["git", "status"], cwd=test_path)

        call_args = mock_run.call_args
        assert call_args[1]["cwd"] == test_path


class TestInitGitRepo:
    """Tests for the init_git_repo function."""

    @patch("maestria.commands.init.run_command")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_init_git_repo_success(self, mock_exists, mock_file, mock_run_command):
        """Test successful git repository initialization."""
        mock_exists.return_value = False
        mock_run_command.return_value = Mock(stdout="", stderr="")

        project_dir = Path("/test/project")
        result = init_git_repo(project_dir)

        assert result is True
        assert mock_run_command.call_count >= 3

    @patch("maestria.commands.init.run_command")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_init_git_repo_with_remote(self, mock_exists, mock_file, mock_run_command):
        """Test git repository initialization with a remote URL."""
        mock_exists.return_value = False
        mock_run_command.return_value = Mock(stdout="", stderr="")

        project_dir = Path("/test/project")
        repo_url = "https://github.com/test/repo.git"
        result = init_git_repo(project_dir, repo_url)

        assert result is True
        assert mock_run_command.call_count >= 4

    @patch("maestria.commands.init.run_command")
    @patch("maestria.commands.init.console")
    def test_init_git_repo_failure(self, mock_console, mock_run_command):
        """Test git repository initialization failure."""
        mock_run_command.side_effect = subprocess.CalledProcessError(1, "git")

        project_dir = Path("/test/project")
        result = init_git_repo(project_dir)

        assert result is False
        assert mock_console.print.called

    @patch("maestria.commands.init.run_command")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_init_git_repo_creates_gitignore(
        self, mock_exists, mock_file, mock_run_command
    ):
        """Test that .gitignore is created if it doesn't exist."""
        mock_exists.return_value = False
        mock_run_command.return_value = Mock(stdout="", stderr="")

        project_dir = Path("/test/project")
        init_git_repo(project_dir)

        mock_file.assert_called_once()
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "__pycache__/" in written_content
        assert ".venv" in written_content


class TestGatherProjectInfo:
    """Tests for the gather_project_info function."""

    @patch("maestria.commands.init.Confirm.ask")
    @patch("maestria.commands.init.Prompt.ask")
    @patch("maestria.commands.init.run_command")
    @patch("maestria.commands.init.console")
    def test_gather_project_info_basic(
        self, mock_console, mock_run_command, mock_prompt, mock_confirm
    ):
        """Test gathering basic project information."""
        mock_run_command.side_effect = [
            Mock(stdout="John Doe"),
            Mock(stdout="john@example.com"),
        ]
        mock_prompt.side_effect = [
            "Test project description",
            "John Doe",
            "john@example.com",
            "test_package",
        ]
        mock_confirm.side_effect = [False]

        result = gather_project_info("test-project")

        assert result["project_description"] == "Test project description"
        assert result["author_name"] == "John Doe"
        assert result["author_email"] == "john@example.com"
        assert result["package_name"] == "test_package"
        assert result["use_git"] is False
        assert result["repo_url"] is None

    @patch("maestria.commands.init.Confirm.ask")
    @patch("maestria.commands.init.Prompt.ask")
    @patch("maestria.commands.init.run_command")
    def test_gather_project_info_with_git_and_remote(
        self, mock_run_command, mock_prompt, mock_confirm
    ):
        """Test gathering project info with git and remote repository."""
        mock_run_command.side_effect = [
            Mock(stdout="John Doe"),
            Mock(stdout="john@example.com"),
        ]
        mock_prompt.side_effect = [
            "Test description",
            "John Doe",
            "john@example.com",
            "test_pkg",
            "https://github.com/test/repo.git",
        ]
        mock_confirm.side_effect = [True, True]

        result = gather_project_info("test-project")

        assert result["use_git"] is True
        assert result["repo_url"] == "https://github.com/test/repo.git"

    @patch("maestria.commands.init.Confirm.ask")
    @patch("maestria.commands.init.Prompt.ask")
    @patch("maestria.commands.init.run_command")
    def test_gather_project_info_no_git_config(
        self, mock_run_command, mock_prompt, mock_confirm
    ):
        """Test gathering project info when git config is not available."""
        mock_run_command.side_effect = subprocess.CalledProcessError(1, "git")
        mock_prompt.side_effect = [
            "Test description",
            "Your Name",
            "your.email@example.com",
            "test_pkg",
        ]
        mock_confirm.side_effect = [False]

        result = gather_project_info("test-project")

        assert "author_name" in result
        assert "author_email" in result

    @patch("maestria.commands.init.Confirm.ask")
    @patch("maestria.commands.init.Prompt.ask")
    @patch("maestria.commands.init.run_command")
    def test_gather_project_info_package_name_conversion(
        self, mock_run_command, mock_prompt, mock_confirm
    ):
        """Test that package name is properly converted from project name."""
        mock_run_command.side_effect = [
            Mock(stdout="John Doe"),
            Mock(stdout="john@example.com"),
        ]
        mock_prompt.side_effect = [
            "Test description",
            "John Doe",
            "john@example.com",
            "my_package",
        ]
        mock_confirm.side_effect = [False]

        gather_project_info("my-project-py")

        assert mock_prompt.call_count == 4


class TestInitializeProject:
    """Tests for the initialize_project function."""

    @patch("maestria.commands.init.init_git_repo")
    @patch("maestria.commands.init.apply_template")
    @patch("maestria.commands.init.gather_project_info")
    @patch("maestria.config.load_config")
    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_basic(
        self,
        mock_exists,
        mock_console,
        mock_load_config,
        mock_gather_info,
        mock_apply_template,
        mock_init_git,
    ):
        """Test basic project initialization."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_gather_info.return_value = {
            "project_description": "Test",
            "author_name": "John",
            "author_email": "john@example.com",
            "package_name": "test_pkg",
            "use_git": False,
            "repo_url": None,
        }
        mock_apply_template.return_value = True

        initialize_project("test-project", "basic", "3.10")

        mock_apply_template.assert_called_once()
        mock_init_git.assert_not_called()

    @patch("maestria.commands.init.init_git_repo")
    @patch("maestria.commands.init.apply_template")
    @patch("maestria.commands.init.gather_project_info")
    @patch("maestria.config.load_config")
    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_with_git(
        self,
        mock_exists,
        mock_console,
        mock_load_config,
        mock_gather_info,
        mock_apply_template,
        mock_init_git,
    ):
        """Test project initialization with git."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_gather_info.return_value = {
            "project_description": "Test",
            "author_name": "John",
            "author_email": "john@example.com",
            "package_name": "test_pkg",
            "use_git": True,
            "repo_url": "https://github.com/test/repo.git",
        }
        mock_apply_template.return_value = True
        mock_init_git.return_value = True

        initialize_project("test-project", "basic", "3.10")

        mock_apply_template.assert_called_once()
        mock_init_git.assert_called_once()

    @patch("maestria.commands.init.get_available_templates")
    @patch("maestria.commands.init.apply_template")
    @patch("maestria.commands.init.gather_project_info")
    @patch("maestria.config.load_config")
    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_template_failure(
        self,
        mock_exists,
        mock_console,
        mock_load_config,
        mock_gather_info,
        mock_apply_template,
        mock_get_templates,
    ):
        """Test project initialization when template application fails."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_gather_info.return_value = {
            "project_description": "Test",
            "author_name": "John",
            "author_email": "john@example.com",
            "package_name": "test_pkg",
            "use_git": False,
            "repo_url": None,
        }
        mock_apply_template.return_value = False
        mock_get_templates.return_value = {"basic": "/path/to/basic"}

        initialize_project("test-project", "nonexistent", "3.10")

        mock_get_templates.assert_called_once()

    @patch("maestria.commands.init.apply_template")
    @patch("maestria.commands.init.gather_project_info")
    @patch("maestria.config.load_config")
    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_plugin_template(
        self,
        mock_exists,
        mock_console,
        mock_load_config,
        mock_gather_info,
        mock_apply_template,
    ):
        """Test project initialization with plugin template."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_gather_info.return_value = {
            "project_description": "Test plugin",
            "author_name": "John",
            "author_email": "john@example.com",
            "package_name": "test_plugin",
            "use_git": False,
            "repo_url": None,
        }
        mock_apply_template.return_value = True

        initialize_project("maestria-test-plugin", "plugin_template", "3.10")

        call_args = mock_apply_template.call_args
        context = call_args[0][3] if len(call_args[0]) > 3 else call_args[1]["context"]

        assert "plugin_name" in context
        assert "plugin_name_short" in context

    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_existing_directory_abort(
        self, mock_exists, mock_console
    ):
        """Test project initialization when directory exists and user aborts."""
        mock_exists.return_value = True
        mock_console.input.return_value = "n"

        initialize_project("test-project", "basic", "3.10")

        assert mock_console.input.called

    @patch("maestria.commands.init.apply_template")
    @patch("maestria.commands.init.gather_project_info")
    @patch("maestria.config.load_config")
    @patch("maestria.commands.init.console")
    @patch("pathlib.Path.exists")
    def test_initialize_project_existing_directory_continue(
        self,
        mock_exists,
        mock_console,
        mock_load_config,
        mock_gather_info,
        mock_apply_template,
    ):
        """Test project initialization when directory exists and user continues."""
        mock_exists.return_value = True
        mock_console.input.return_value = "y"
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_gather_info.return_value = {
            "project_description": "Test",
            "author_name": "John",
            "author_email": "john@example.com",
            "package_name": "test_pkg",
            "use_git": False,
            "repo_url": None,
        }
        mock_apply_template.return_value = True

        initialize_project("test-project", "basic", "3.10")

        mock_apply_template.assert_called_once()
