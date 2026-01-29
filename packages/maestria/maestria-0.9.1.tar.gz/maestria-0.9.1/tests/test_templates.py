"""Tests for the Maestria template system."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import git

from maestria.config import MaestriaTemplateConfig
from maestria.templates import (
    apply_template,
    cleanup_template_path,
    get_available_templates,
    get_template_path,
    process_template_files,
)


class TestGetAvailableTemplates:
    """Tests for get_available_templates function."""

    def test_get_available_templates_empty(self):
        """Test getting available templates when none configured."""
        config = Mock()
        config.maestria.template_registry = {}
        templates = get_available_templates(config)
        assert templates == {}

    def test_get_available_templates_with_templates(self):
        """Test getting available templates."""
        config = Mock()
        config.maestria.template_registry = {
            "basic": MaestriaTemplateConfig(type="local", path="basic"),
            "plugin": MaestriaTemplateConfig(type="local", path="plugin"),
        }
        templates = get_available_templates(config)
        assert len(templates) == 2
        assert "basic" in templates
        assert "plugin" in templates


class TestGetTemplatePath:
    """Tests for get_template_path function."""

    def test_get_template_path_local_absolute(self):
        """Test getting template path for local absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "mytemplate"
            template_path.mkdir()

            config = Mock()
            config.maestria.template_registry = {
                "test": MaestriaTemplateConfig(type="local", path=str(template_path))
            }

            result = get_template_path("test", config)
            assert result.resolve() == template_path.resolve()

    def test_get_template_path_local_relative(self):
        """Test getting template path for local relative path."""
        config = Mock()
        config.maestria.template_registry = {
            "basic": MaestriaTemplateConfig(type="local", path="basic")
        }

        result = get_template_path("basic", config)
        if result:
            assert "basic" in str(result)

    def test_get_template_path_builtin_fallback(self):
        """Test fallback to built-in templates."""
        config = Mock()
        config.maestria.template_registry = {}

        result = get_template_path("basic", config)
        assert result is None or "basic" in str(result)

    @patch("git.Repo.clone_from")
    def test_get_template_path_git_success(self, mock_clone):
        """Test getting template from git repository."""
        with tempfile.TemporaryDirectory():
            mock_repo = Mock()
            mock_clone.return_value = mock_repo

            config = Mock()
            config.maestria.template_registry = {
                "remote": MaestriaTemplateConfig(
                    type="git",
                    repo_url="https://github.com/org/templates",
                    ref="main",
                )
            }

            def clone_side_effect(url, path, **kwargs):
                Path(path).mkdir(exist_ok=True)
                return mock_repo

            mock_clone.side_effect = clone_side_effect

            result = get_template_path("remote", config)
            assert result is not None
            mock_clone.assert_called_once()

    @patch("git.Repo.clone_from")
    def test_get_template_path_git_with_subdirectory(self, mock_clone):
        """Test getting template from git repository with subdirectory."""
        with tempfile.TemporaryDirectory():
            mock_repo = Mock()
            mock_clone.return_value = mock_repo

            config = Mock()
            config.maestria.template_registry = {
                "remote": MaestriaTemplateConfig(
                    type="git",
                    repo_url="https://github.com/org/templates",
                    ref="main",
                    directory="python/basic",
                )
            }

            def clone_side_effect(url, path, **kwargs):
                clone_path = Path(path)
                clone_path.mkdir(exist_ok=True)
                subdir = clone_path / "python" / "basic"
                subdir.mkdir(parents=True, exist_ok=True)
                return mock_repo

            mock_clone.side_effect = clone_side_effect

            result = get_template_path("remote", config)
            assert result is not None
            assert "python" in str(result)
            assert "basic" in str(result)

    @patch("git.Repo.clone_from")
    @patch("maestria.templates.console")
    def test_get_template_path_git_clone_error(self, mock_console, mock_clone):
        """Test handling git clone errors."""
        mock_clone.side_effect = git.GitCommandError("clone", "error")

        config = Mock()
        config.maestria.template_registry = {
            "remote": MaestriaTemplateConfig(
                type="git",
                repo_url="https://github.com/org/templates",
                ref="main",
            )
        }

        result = get_template_path("remote", config)
        assert result is None
        mock_console.print.assert_called()

    @patch("git.Repo.clone_from")
    @patch("maestria.templates.console")
    def test_get_template_path_git_directory_not_found(self, mock_console, mock_clone):
        """Test when git clone succeeds but subdirectory doesn't exist."""
        with tempfile.TemporaryDirectory():
            mock_repo = Mock()
            mock_clone.return_value = mock_repo

            config = Mock()
            config.maestria.template_registry = {
                "remote": MaestriaTemplateConfig(
                    type="git",
                    repo_url="https://github.com/org/templates",
                    ref="main",
                    directory="nonexistent",
                )
            }

            def clone_side_effect(url, path, **kwargs):
                Path(path).mkdir(exist_ok=True)
                return mock_repo

            mock_clone.side_effect = clone_side_effect

            result = get_template_path("remote", config)
            assert result is None


class TestCleanupTemplatePath:
    """Tests for cleanup_template_path function."""

    def test_cleanup_template_path_temp_directory(self):
        """Test cleanup of temporary directory."""
        tmpdir = tempfile.mkdtemp(prefix="maestria_template_")
        tmppath = Path(tmpdir)
        assert tmppath.exists()

        cleanup_template_path(tmppath)
        assert not tmppath.exists()

    def test_cleanup_template_path_non_temp_directory(self):
        """Test cleanup removes any directory under temp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "mydir"
            test_dir.mkdir()

            cleanup_template_path(test_dir)
            # cleanup_template_path will remove anything under tempdir
            assert not test_dir.exists()

    @patch("maestria.templates.console")
    def test_cleanup_template_path_error(self, mock_console):
        """Test cleanup error handling."""
        mock_path = Mock()
        mock_path.__str__ = lambda x: tempfile.gettempdir() + "/test"

        with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
            cleanup_template_path(mock_path)
            mock_console.print.assert_called()


class TestProcessTemplateFiles:
    """Tests for process_template_files function."""

    def test_process_template_files_basic(self):
        """Test basic template file processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            test_file = tmpdir_path / "test.py"
            with open(test_file, "w") as f:
                f.write("# Project: {{project_name}}\n")
                f.write("VERSION = '{{version}}'\n")

            context = {"project_name": "MyProject", "version": "1.0.0"}
            process_template_files(tmpdir_path, context)

            with open(test_file, "r") as f:
                content = f.read()
            assert "MyProject" in content
            assert "1.0.0" in content
            assert "{{project_name}}" not in content
            assert "{{version}}" not in content

    def test_process_template_files_directory_rename(self):
        """Test directory name replacement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            template_dir = tmpdir_path / "{{package_name}}"
            template_dir.mkdir()

            context = {"package_name": "mypackage"}
            process_template_files(tmpdir_path, context)

            new_dir = tmpdir_path / "mypackage"
            assert new_dir.exists()
            assert not template_dir.exists()

    def test_process_template_files_multiple_extensions(self):
        """Test processing files with different extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            files = {
                "test.py": "name = '{{project_name}}'",
                "README.md": "# {{project_name}}",
                "config.toml": "name = '{{project_name}}'",
                "data.json": '{"name": "{{project_name}}"}',
            }

            for filename, content in files.items():
                with open(tmpdir_path / filename, "w") as f:
                    f.write(content)

            context = {"project_name": "TestProject"}
            process_template_files(tmpdir_path, context)

            for filename in files.keys():
                with open(tmpdir_path / filename, "r") as f:
                    content = f.read()
                assert "TestProject" in content
                assert "{{project_name}}" not in content

    @patch.dict("os.environ", {"MAESTRIA_VERBOSE": "1"})
    @patch("maestria.templates.console")
    def test_process_template_files_verbose(self, mock_console):
        """Test verbose output during template processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            test_file = tmpdir_path / "test.py"
            with open(test_file, "w") as f:
                f.write("{{project_name}}")

            context = {"project_name": "Test", "package_name": "test"}
            process_template_files(tmpdir_path, context)

            mock_console.print.assert_called()

    @patch("maestria.templates.console")
    def test_process_template_files_read_error(self, mock_console):
        """Test handling file read errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            test_file = tmpdir_path / "test.py"
            test_file.write_text("{{project_name}}")

            with patch("builtins.open", side_effect=OSError("Read error")):
                context = {"project_name": "Test"}
                process_template_files(tmpdir_path, context)

                assert any(
                    "Warning" in str(call) for call in mock_console.print.call_args_list
                )


class TestApplyTemplate:
    """Tests for apply_template function."""

    @patch("maestria.templates.get_template_path")
    @patch("subprocess.run")
    def test_apply_template_success(self, mock_subprocess, mock_get_path):
        """Test successful template application."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as template_tmpdir,
        ):
            tmpdir_path = Path(tmpdir)
            template_path = Path(template_tmpdir)

            (template_path / "pyproject.toml").write_text(
                "[project]\nname = '{{project_name}}'"
            )
            (template_path / "README.md").write_text("# {{project_name}}")

            mock_get_path.return_value = template_path
            mock_subprocess.return_value = Mock(returncode=0)

            config = Mock()
            config.maestria.template_registry = {}
            config.maestria.src_layout = False

            context = {
                "project_name": "test",
                "project_slug": "test",
                "project_dir": "test",
            }

            result = apply_template("basic", tmpdir_path, config, context)
            assert result is True

            project_dir = tmpdir_path / "test"
            assert project_dir.exists()
            assert (project_dir / "pyproject.toml").exists()
            assert (project_dir / "README.md").exists()

    @patch("maestria.templates.get_template_path")
    @patch("maestria.templates.console")
    def test_apply_template_not_found(self, mock_console, mock_get_path):
        """Test template not found."""
        mock_get_path.return_value = None

        config = Mock()
        config.maestria.template_registry = {"other": MaestriaTemplateConfig()}

        context = {"project_name": "test"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = apply_template("nonexistent", Path(tmpdir), config, context)
            assert result is False
            mock_console.print.assert_called()

    @patch("maestria.templates.get_template_path")
    @patch("subprocess.run")
    def test_apply_template_with_src_layout(self, mock_subprocess, mock_get_path):
        """Test template application with src layout."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as template_tmpdir,
        ):
            tmpdir_path = Path(tmpdir)
            template_path = Path(template_tmpdir)

            src_dir = template_path / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")

            mock_get_path.return_value = template_path
            mock_subprocess.return_value = Mock(returncode=0)

            config = Mock()
            config.maestria.template_registry = {}
            config.maestria.src_layout = True

            context = {
                "project_name": "test",
                "project_slug": "test",
                "project_dir": "test",
            }

            result = apply_template("basic", tmpdir_path, config, context)
            assert result is True

            project_dir = tmpdir_path / "test"
            assert (project_dir / "src").exists()

    @patch("maestria.templates.get_template_path")
    @patch("subprocess.run")
    def test_apply_template_flat_layout(self, mock_subprocess, mock_get_path):
        """Test template application with flat layout."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as template_tmpdir,
        ):
            tmpdir_path = Path(tmpdir)
            template_path = Path(template_tmpdir)

            src_dir = template_path / "src" / "myproject"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("# Init")

            mock_get_path.return_value = template_path
            mock_subprocess.return_value = Mock(returncode=0)

            config = Mock()
            config.maestria.template_registry = {}
            config.maestria.src_layout = False

            context = {
                "project_name": "test",
                "project_slug": "myproject",
                "project_dir": "test",
            }

            result = apply_template("basic", tmpdir_path, config, context)
            assert result is True

            project_dir = tmpdir_path / "test"
            assert (project_dir / "__init__.py").exists()

    @patch("maestria.templates.get_template_path")
    @patch("subprocess.run")
    def test_apply_template_venv_creation_error(self, mock_subprocess, mock_get_path):
        """Test handling venv creation errors."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as template_tmpdir,
        ):
            tmpdir_path = Path(tmpdir)
            template_path = Path(template_tmpdir)

            (template_path / "README.md").write_text("# Test")

            mock_get_path.return_value = template_path
            mock_subprocess.side_effect = [
                subprocess.CalledProcessError(1, "uv"),
                Mock(returncode=0),
            ]

            config = Mock()
            config.maestria.template_registry = {}
            config.maestria.src_layout = False

            context = {
                "project_name": "test",
                "project_slug": "test",
                "project_dir": "test",
            }

            result = apply_template("basic", tmpdir_path, config, context)
            assert result is True

    @patch("maestria.templates.get_template_path")
    @patch("maestria.templates.console")
    def test_apply_template_general_error(self, mock_console, mock_get_path):
        """Test handling general errors during template application."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path("/nonexistent/path")

            config = Mock()
            config.maestria.template_registry = {}

            context = {"project_name": "test", "project_slug": "test"}

            result = apply_template("basic", Path(tmpdir), config, context)
            assert result is False
            mock_console.print.assert_called()

    @patch("maestria.templates.get_template_path")
    @patch("maestria.templates.cleanup_template_path")
    def test_apply_template_cleanup_on_success(self, mock_cleanup, mock_get_path):
        """Test template cleanup is called on success."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as template_tmpdir,
        ):
            tmpdir_path = Path(tmpdir)
            template_path = Path(template_tmpdir)

            (template_path / "README.md").write_text("# Test")

            mock_get_path.return_value = template_path

            config = Mock()
            config.maestria.template_registry = {}
            config.maestria.src_layout = False

            context = {
                "project_name": "test",
                "project_slug": "test",
                "project_dir": "test",
            }

            with patch("subprocess.run"):
                apply_template("basic", tmpdir_path, config, context)
                mock_cleanup.assert_called_with(template_path)

    @patch("maestria.templates.get_template_path")
    @patch("maestria.templates.cleanup_template_path")
    def test_apply_template_cleanup_on_error(self, mock_cleanup, mock_get_path):
        """Test template cleanup is called on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path("/nonexistent")
            mock_get_path.return_value = template_path

            config = Mock()
            context = {"project_name": "test"}

            apply_template("basic", Path(tmpdir), config, context)
            mock_cleanup.assert_called_with(template_path)
