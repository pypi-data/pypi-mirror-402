"""Tests for the Maestria configuration system."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from maestria.config import (
    MaestriaConfig,
    MaestriaProjectConfig,
    MaestriaTemplateConfig,
    TeamConstants,
    find_config,
    load_config,
)


class TestMaestriaTemplateConfig:
    """Tests for MaestriaTemplateConfig model."""

    def test_default_values(self):
        """Test template config with default values."""
        config = MaestriaTemplateConfig()
        assert config.type == "local"
        assert config.path is None
        assert config.repo_url is None
        assert config.ref == "main"
        assert config.directory is None

    def test_custom_values(self):
        """Test template config with custom values."""
        config = MaestriaTemplateConfig(
            type="git",
            repo_url="https://github.com/org/repo",
            ref="develop",
            directory="templates/python",
        )
        assert config.type == "git"
        assert config.repo_url == "https://github.com/org/repo"
        assert config.ref == "develop"
        assert config.directory == "templates/python"


class TestTeamConstants:
    """Tests for TeamConstants model."""

    def test_default_values(self):
        """Test team constants with default values."""
        constants = TeamConstants()
        assert constants.pypi_repo is None
        assert constants.docker_hub_account is None

    def test_custom_values(self):
        """Test team constants with custom values."""
        constants = TeamConstants(pypi_repo="internal-pypi", docker_hub_account="myorg")
        assert constants.pypi_repo == "internal-pypi"
        assert constants.docker_hub_account == "myorg"


class TestMaestriaConfig:
    """Tests for MaestriaConfig model."""

    def test_default_values(self):
        """Test maestria config with default values."""
        config = MaestriaConfig()
        assert config.template_registry == {}
        assert config.hooks == {"pre_command": [], "post_command": []}
        assert config.src_layout is False
        assert isinstance(config.constants, TeamConstants)


class TestFindConfig:
    """Tests for find_config function."""

    def test_find_config_not_found(self):
        """Test finding a configuration file when none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            assert find_config() is None

    def test_find_config_in_current_dir(self):
        """Test finding a configuration file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write('[project]\nname = "test-project"\n')

            os.chdir(tmpdir)
            found_config = find_config()

            assert found_config.resolve() == config_path.resolve()

    def test_find_config_in_parent_dir(self):
        """Test finding a configuration file in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"
            subdir = tmpdir_path / "subdir"
            subdir.mkdir()

            with open(config_path, "w") as f:
                f.write('[project]\nname = "test-project"\n')

            os.chdir(subdir)
            found_config = find_config()

            assert found_config.resolve() == config_path.resolve()


class TestLoadConfig:
    """Tests for load_config function."""

    @patch("maestria.config.find_config")
    def test_load_config_not_found(self, mock_find):
        """Test loading config when no file is found."""
        mock_find.return_value = None
        config = load_config()
        assert isinstance(config, MaestriaProjectConfig)
        assert config.path is None

    def test_load_config_found(self):
        """Test loading config when file is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write('[project]\nname = "test-project"\nversion = "1.0.0"\n')

            os.chdir(tmpdir)
            config = load_config()

            assert config.name == "test-project"
            assert config.version == "1.0.0"


class TestMaestriaProjectConfig:
    """Tests for MaestriaProjectConfig class."""

    def test_init_no_path(self):
        """Test initialization without a path."""
        config = MaestriaProjectConfig()
        assert config.path is None
        assert config.data == {}
        assert isinstance(config.maestria, MaestriaConfig)

    def test_init_with_path(self):
        """Test initialization with a path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write("""
[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
requires-python = ">=3.10"

[[project.authors]]
name = "Test Author"
email = "test@example.com"

[project.dependencies]
requests = "^2.25.1"

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0",
    "black>=21.5b2"
]

[tool.maestria]

[tool.maestria.template_registry]
test-template = { type = "local", path = "test-template" }
""")

            config = MaestriaProjectConfig(config_path)

            assert config.name == "test-project"
            assert config.version == "0.1.0"
            assert config.description == "Test project"
            assert config.python_version == "3.10"
            assert len(config.authors) == 1
            assert config.authors[0]["name"] == "Test Author"
            assert config.authors[0]["email"] == "test@example.com"
            assert "test-template" in config.maestria.template_registry

    def test_init_with_invalid_toml(self):
        """Test initialization with invalid TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write("invalid toml content [[[")

            config = MaestriaProjectConfig(config_path)
            assert config.data == {}

    def test_name_from_data(self):
        """Test getting name from data."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"name": "my-project"}}
        assert config.name == "my-project"

    def test_name_from_path(self):
        """Test getting name from path when not in data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            config_path.touch()
            config = MaestriaProjectConfig(config_path)
            assert config.name == Path(tmpdir).name

    def test_name_from_cwd(self):
        """Test getting name from cwd as fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            config = MaestriaProjectConfig()
            current_dir = Path(tmpdir).name
            assert config.name == current_dir

    @patch("os.getcwd")
    def test_name_fallback(self, mock_getcwd):
        """Test name fallback when cwd fails."""
        mock_getcwd.side_effect = OSError()
        config = MaestriaProjectConfig()
        assert config.name == "maestria-project"

    def test_version(self):
        """Test getting version."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"version": "2.0.0"}}
        assert config.version == "2.0.0"

    def test_version_default(self):
        """Test default version."""
        config = MaestriaProjectConfig()
        assert config.version == "0.1.0"

    def test_python_version_with_gte(self):
        """Test parsing Python version with >=."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"requires-python": ">=3.9"}}
        assert config.python_version == "3.9"

    def test_python_version_with_complex_requirement(self):
        """Test parsing Python version with complex requirement."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"requires-python": ">=3.10,<4.0"}}
        assert config.python_version == "3.10"

    def test_python_version_default(self):
        """Test default Python version."""
        config = MaestriaProjectConfig()
        assert config.python_version == "3.10"

    def test_description(self):
        """Test getting description."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"description": "Test description"}}
        assert config.description == "Test description"

    def test_description_default(self):
        """Test default description."""
        config = MaestriaProjectConfig()
        assert config.description == ""

    def test_authors(self):
        """Test getting authors."""
        config = MaestriaProjectConfig()
        config.data = {
            "project": {"authors": [{"name": "John", "email": "john@example.com"}]}
        }
        assert len(config.authors) == 1
        assert config.authors[0]["name"] == "John"

    def test_authors_default(self):
        """Test default authors."""
        config = MaestriaProjectConfig()
        assert config.authors == []

    def test_dependencies(self):
        """Test getting dependencies."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"dependencies": ["click>=8.0", "rich>=10.0"]}}
        assert len(config.dependencies) == 2

    def test_dependencies_default(self):
        """Test default dependencies."""
        config = MaestriaProjectConfig()
        assert config.dependencies == []

    def test_dev_dependencies(self):
        """Test getting dev dependencies."""
        config = MaestriaProjectConfig()
        config.data = {
            "project": {"optional-dependencies": {"dev": ["pytest", "black"]}}
        }
        assert len(config.dev_dependencies) == 2

    def test_dev_dependencies_default(self):
        """Test default dev dependencies."""
        config = MaestriaProjectConfig()
        assert config.dev_dependencies == []

    def test_scripts(self):
        """Test getting scripts."""
        config = MaestriaProjectConfig()
        config.data = {
            "tool": {"maestria": {"scripts": {"test": "pytest", "lint": "black ."}}}
        }
        assert len(config.scripts) == 2
        assert config.scripts["test"] == "pytest"

    def test_scripts_default(self):
        """Test default scripts."""
        config = MaestriaProjectConfig()
        assert config.scripts == {}

    def test_pypi_repo(self):
        """Test getting PyPI repo."""
        config = MaestriaProjectConfig()
        config.maestria.constants.pypi_repo = "internal-pypi"
        assert config.pypi_repo == "internal-pypi"

    def test_docker_hub_account(self):
        """Test getting Docker Hub account."""
        config = MaestriaProjectConfig()
        config.maestria.constants.docker_hub_account = "myorg"
        assert config.docker_hub_account == "myorg"

    def test_author_property(self):
        """Test getting author from authors list."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"authors": [{"name": "John Doe"}]}}
        assert config.author == "John Doe"

    def test_author_property_empty(self):
        """Test getting author when no authors."""
        config = MaestriaProjectConfig()
        assert config.author is None

    def test_author_email_property(self):
        """Test getting author email from authors list."""
        config = MaestriaProjectConfig()
        config.data = {"project": {"authors": [{"email": "john@example.com"}]}}
        assert config.author_email == "john@example.com"

    def test_author_email_property_empty(self):
        """Test getting author email when no authors."""
        config = MaestriaProjectConfig()
        assert config.author_email is None

    def test_root_dir_with_path(self):
        """Test getting root dir with path set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            config_path.touch()
            config = MaestriaProjectConfig(config_path)
            assert config.root_dir == Path(tmpdir)

    def test_root_dir_without_path(self):
        """Test getting root dir without path set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            config = MaestriaProjectConfig()
            assert config.root_dir.resolve() == Path(tmpdir).resolve()

    @patch("subprocess.run")
    def test_get_git_info_https(self, mock_run):
        """Test getting git info from HTTPS URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            mock_run.return_value = Mock(
                stdout="https://github.com/myorg/myrepo.git\n", returncode=0
            )
            config = MaestriaProjectConfig()
            git_info = config.get_git_info()
            assert git_info["org"] == "myorg"
            assert git_info["repo"] == "myrepo"

    @patch("subprocess.run")
    def test_get_git_info_ssh(self, mock_run):
        """Test getting git info from SSH URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            mock_run.return_value = Mock(
                stdout="git@githost.example:myorg/myrepo.git\n", returncode=0
            )
            config = MaestriaProjectConfig()
            git_info = config.get_git_info()
            assert git_info["org"] == "myorg"
            assert git_info["repo"] == "myrepo"

    @patch("subprocess.run")
    def test_get_git_info_not_a_repo(self, mock_run):
        """Test getting git info when not a git repo."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        config = MaestriaProjectConfig()
        git_info = config.get_git_info()
        assert git_info["org"] is None
        assert git_info["repo"] is None

    @patch("subprocess.run")
    def test_get_git_info_git_not_installed(self, mock_run):
        """Test getting git info when git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        config = MaestriaProjectConfig()
        git_info = config.get_git_info()
        assert git_info["org"] is None
        assert git_info["repo"] is None

    @patch.dict(
        "os.environ", {"PYPI_REPO": "env-pypi", "DOCKER_HUB_ACCOUNT": "env-docker"}
    )
    def test_env_overrides_config(self):
        """Test that environment variables override config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write("""
[project]
name = "test"

[tool.maestria.constants]
pypi_repo = "config-pypi"
docker_hub_account = "config-docker"
""")

            config = MaestriaProjectConfig(config_path)
            assert config.pypi_repo == "env-pypi"
            assert config.docker_hub_account == "env-docker"

    def test_hooks_configuration(self):
        """Test loading hooks configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write("""
[project]
name = "test"

[tool.maestria.hooks]
pre_command = ["echo before"]
post_command = ["echo after"]
""")

            config = MaestriaProjectConfig(config_path)
            assert config.maestria.hooks["pre_command"] == ["echo before"]
            assert config.maestria.hooks["post_command"] == ["echo after"]

    def test_multiple_template_registry_entries(self):
        """Test loading multiple template registry entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_path = tmpdir_path / "pyproject.toml"

            with open(config_path, "w") as f:
                f.write("""
[project]
name = "test"

[tool.maestria.template_registry]
local-template = { type = "local", path = "./templates/basic" }
git-template = { type = "git", repo_url = "https://github.com/org/templates", ref = "main" }
""")

            config = MaestriaProjectConfig(config_path)
            assert len(config.maestria.template_registry) == 2
            assert config.maestria.template_registry["local-template"].type == "local"
            assert config.maestria.template_registry["git-template"].type == "git"
            assert config.maestria.template_registry["git-template"].ref == "main"
