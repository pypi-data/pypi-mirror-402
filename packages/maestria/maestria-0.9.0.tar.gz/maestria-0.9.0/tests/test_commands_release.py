"""Tests for release command."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.commands.release import (
    check_dependencies,
    clean_build_dirs,
    get_pypi_repo,
    install_missing_dependencies,
    release_project,
    run_bump_version,
    run_tests,
)


class TestGetPypiRepo:
    """Tests for get_pypi_repo function."""

    def test_get_pypi_repo_from_config(self):
        """Test getting PyPI repo from config."""
        config = Mock()
        config.pypi_repo = "internal-pypi"

        result = get_pypi_repo(config)
        assert result == "internal-pypi"

    def test_get_pypi_repo_none(self):
        """Test when PyPI repo is not configured."""
        config = Mock()
        config.pypi_repo = None

        result = get_pypi_repo(config)
        assert result is None

    @patch.dict("os.environ", {"PYPI_REPO": "env-pypi"})
    def test_get_pypi_repo_from_env(self):
        """Test getting PyPI repo from environment."""
        config = Mock()
        config.pypi_repo = "env-pypi"

        result = get_pypi_repo(config)
        assert result == "env-pypi"


class TestCleanBuildDirs:
    """Tests for clean_build_dirs function."""

    def test_clean_build_dirs_removes_directories(self):
        """Test that build directories are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Create build directories
            (project_dir / "build").mkdir()
            (project_dir / "dist").mkdir()
            (project_dir / "build" / "lib").mkdir()
            (project_dir / "dist" / "package.whl").touch()

            clean_build_dirs(project_dir)

            assert not (project_dir / "build").exists()
            assert not (project_dir / "dist").exists()

    def test_clean_build_dirs_no_directories(self):
        """Test clean when directories don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Should not raise error
            clean_build_dirs(project_dir)


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_deps_util")
    def test_check_dependencies_all_present(self, mock_check_util, mock_activate):
        """Test when all dependencies are present."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_check_util.return_value = (True, [])

        all_installed, missing = check_dependencies(Path("/tmp/project"), verbose=False)

        assert all_installed is True
        assert missing == []

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_deps_util")
    def test_check_dependencies_missing(self, mock_check_util, mock_activate):
        """Test when dependencies are missing."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_check_util.return_value = (False, ["pytest", "build"])

        all_installed, missing = check_dependencies(Path("/tmp/project"), verbose=True)

        assert all_installed is False
        assert "pytest" in missing

    @patch("maestria.commands.release.check_deps_util")
    def test_check_dependencies_error(self, mock_check_util):
        """Test when dependency check fails."""
        mock_check_util.side_effect = Exception("Check error")

        all_installed, missing = check_dependencies(Path("/tmp/project"), verbose=False)

        assert all_installed is False
        assert len(missing) == 4


class TestInstallMissingDependencies:
    """Tests for install_missing_dependencies function."""

    def test_install_no_dependencies(self, tmp_path):
        """Test with empty dependency list."""
        result = install_missing_dependencies(tmp_path, [], verbose=False)

        assert result is True

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.install_deps_util")
    @patch("maestria.commands.release.verify_dependencies")
    def test_install_dependencies_success(
        self, mock_verify, mock_install, mock_activate
    ):
        """Test successful dependency installation."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_install.return_value = True
        mock_verify.return_value = (True, [])

        result = install_missing_dependencies(
            Path("/tmp/project"), ["pytest", "build"], verbose=False
        )

        assert result is True

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.install_deps_util")
    def test_install_dependencies_install_failed(self, mock_install, mock_activate):
        """Test when installation fails."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_install.return_value = False

        result = install_missing_dependencies(
            Path("/tmp/project"), ["pytest"], verbose=False
        )

        assert result is False

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.install_deps_util")
    @patch("maestria.commands.release.verify_dependencies")
    def test_install_dependencies_verify_failed(
        self, mock_verify, mock_install, mock_activate
    ):
        """Test when verification fails after installation."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_install.return_value = True
        mock_verify.return_value = (False, ["pytest"])

        result = install_missing_dependencies(
            Path("/tmp/project"), ["pytest"], verbose=False
        )

        assert result is False


class TestRunTests:
    """Tests for run_tests function."""

    @patch("maestria.commands.test.run_tests")
    def test_run_tests_success(self, mock_run_tests):
        """Test successful test run."""
        mock_run_tests.return_value = None

        result = run_tests(Path("/tmp/project"), verbose=False)

        assert result is True

    @patch("maestria.commands.test.run_tests")
    @patch("maestria.commands.release.console")
    def test_run_tests_failure_abort(self, mock_console, mock_run_tests):
        """Test test failure with abort."""
        mock_run_tests.side_effect = Exception("Tests failed")
        mock_console.input.return_value = "n"

        result = run_tests(Path("/tmp/project"), verbose=False)

        assert result is False

    @patch("maestria.commands.test.run_tests")
    @patch("maestria.commands.release.console")
    def test_run_tests_failure_continue(self, mock_console, mock_run_tests):
        """Test test failure with continue."""
        mock_run_tests.side_effect = Exception("Tests failed")
        mock_console.input.return_value = "y"

        result = run_tests(Path("/tmp/project"), verbose=False)

        assert result is True


class TestRunBumpVersion:
    """Tests for run_bump_version function."""

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.bump_version")
    def test_bump_version_success(self, mock_bump, mock_activate):
        """Test successful version bump."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_bump.return_value = ("1.0.0", "1.0.1")

        result = run_bump_version(Path("/tmp/project"), "patch", verbose=False)

        assert result == "1.0.1"

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.bump_version")
    def test_bump_version_failed(self, mock_bump, mock_activate):
        """Test failed version bump."""
        mock_activate.return_value = {"venv_path": Path("/tmp/.venv")}
        mock_bump.return_value = None

        result = run_bump_version(Path("/tmp/project"), "patch", verbose=False)

        assert result is None

    @patch("maestria.commands.release.activate_environment")
    def test_bump_version_env_error(self, mock_activate):
        """Test environment activation error."""
        mock_activate.side_effect = RuntimeError("No venv")

        result = run_bump_version(Path("/tmp/project"), "patch", verbose=False)

        assert result is None


class TestReleaseProject:
    """Tests for release_project function."""

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.console")
    def test_release_project_missing_dependencies_no_install(
        self, mock_console, mock_check, mock_activate
    ):
        """Test release when dependencies missing and auto-install disabled."""
        config = Mock()
        config.root_dir = Path("/tmp/test")

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (False, ["pytest", "build"])

        release_project(config, bump="patch", install_deps=False)

        mock_console.print.assert_called()

    @patch("maestria.commands.release.activate_environment")
    def test_release_project_no_venv(self, mock_activate):
        """Test release when virtual environment doesn't exist."""
        config = Mock()
        config.root_dir = Path("/tmp/test")

        mock_activate.side_effect = RuntimeError("No venv")

        release_project(config, bump="patch", install_deps=False)

        mock_activate.assert_called_once()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.install_missing_dependencies")
    @patch("maestria.commands.release.console")
    def test_release_project_install_deps_failed(
        self, mock_console, mock_install, mock_check, mock_activate
    ):
        """Test release when dependency installation fails."""
        config = Mock()
        config.root_dir = Path("/tmp/test")

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (False, ["pytest"])
        mock_install.return_value = False

        release_project(config, bump="patch", install_deps=True)

        mock_install.assert_called_once()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.console")
    def test_release_project_tests_failed(
        self,
        mock_console,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test release when tests fail."""
        config = Mock()
        config.root_dir = Path("/tmp/test")

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = False

        release_project(config, bump="patch", install_deps=False)

        mock_run_tests.assert_called_once()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.run_bump_version")
    @patch("maestria.commands.release.console")
    def test_release_project_bump_failed(
        self,
        mock_console,
        mock_bump,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test release when version bump fails."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.version = "1.0.0"

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = True
        mock_bump.return_value = None

        release_project(config, bump="patch", install_deps=False)

        mock_bump.assert_called_once()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.run_bump_version")
    @patch("subprocess.run")
    @patch("maestria.commands.release.console")
    def test_release_project_git_push_failed(
        self,
        mock_console,
        mock_subprocess,
        mock_bump,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test release when git push fails."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.version = "1.0.0"

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = True
        mock_bump.return_value = "1.0.1"
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git")
        mock_console.input.return_value = "n"

        release_project(config, bump="patch", install_deps=False)

        mock_subprocess.assert_called()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.run_bump_version")
    @patch("subprocess.run")
    @patch("maestria.commands.release.run_in_environment")
    @patch("maestria.commands.release.console")
    def test_release_project_build_failed(
        self,
        mock_console,
        mock_run_env,
        mock_subprocess,
        mock_bump,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test release when build fails."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.version = "1.0.0"

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = True
        mock_bump.return_value = "1.0.1"
        mock_subprocess.return_value = subprocess.CompletedProcess([], 0)
        mock_run_env.side_effect = subprocess.CalledProcessError(1, "build")

        release_project(config, bump="patch", install_deps=False)

        mock_run_env.assert_called()

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.run_bump_version")
    @patch("subprocess.run")
    @patch("maestria.commands.release.run_in_environment")
    @patch("maestria.commands.release.console")
    def test_release_project_success_no_publish(
        self,
        mock_console,
        mock_run_env,
        mock_subprocess,
        mock_bump,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test successful release without publishing."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.version = "1.0.0"

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = True
        mock_bump.return_value = "1.0.1"
        mock_subprocess.return_value = subprocess.CompletedProcess([], 0)
        mock_run_env.return_value = None
        mock_console.input.return_value = "n"

        release_project(config, bump="patch", install_deps=False)

        assert mock_run_env.call_count == 1

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.run_bump_version")
    @patch("subprocess.run")
    @patch("maestria.commands.release.run_in_environment")
    @patch("maestria.commands.release.console")
    def test_release_project_success_with_publish(
        self,
        mock_console,
        mock_run_env,
        mock_subprocess,
        mock_bump,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test successful release with publishing."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.version = "1.0.0"

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = "test-pypi"
        mock_run_tests.return_value = True
        mock_bump.return_value = "1.0.1"
        mock_subprocess.return_value = subprocess.CompletedProcess([], 0)
        mock_run_env.return_value = None
        mock_console.input.side_effect = ["y", "y"]

        release_project(config, bump="patch", install_deps=False)

        assert mock_run_env.call_count == 2

    @patch("maestria.commands.release.activate_environment")
    @patch("maestria.commands.release.check_dependencies")
    @patch("maestria.commands.release.get_pypi_repo")
    @patch("maestria.commands.release.clean_build_dirs")
    @patch("maestria.commands.release.run_tests")
    @patch("maestria.commands.release.console")
    def test_release_project_no_pypi_repo_prompt(
        self,
        mock_console,
        mock_run_tests,
        mock_clean,
        mock_pypi,
        mock_check,
        mock_activate,
    ):
        """Test release when PyPI repo not configured."""
        config = Mock()
        config.root_dir = Path("/tmp/test")
        config.pypi_repo = None

        mock_activate.return_value = {"python_path": Path("/tmp/.venv/bin/python")}
        mock_check.return_value = (True, [])
        mock_pypi.return_value = None
        mock_run_tests.return_value = False
        mock_console.input.return_value = "my-repo"

        release_project(config, bump="patch", install_deps=False)

        mock_console.input.assert_called()
