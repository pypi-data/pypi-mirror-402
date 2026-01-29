import os
import sys
from unittest.mock import Mock, patch

from maestria.utils.dependencies import check_dependencies, main, verify_dependencies


class TestCheckDependencies:

    def test_all_dependencies_present(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()

            all_installed, missing = check_dependencies(
                tmp_path, venv_path, verbose=False
            )

            assert all_installed is True
            assert missing == []

    def test_missing_modules(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        def mock_find_spec(name):
            if name == "pytest":
                return None
            return Mock()

        with patch("importlib.util.find_spec", side_effect=mock_find_spec):
            all_installed, missing = check_dependencies(
                tmp_path, venv_path, verbose=False
            )

            assert all_installed is False
            assert "pytest" in missing

    def test_missing_cli_tools(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()

            all_installed, missing = check_dependencies(
                tmp_path, venv_path, verbose=False
            )

            assert all_installed is False
            assert "bump2version" in missing

    def test_all_missing(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            all_installed, missing = check_dependencies(
                tmp_path, venv_path, verbose=False
            )

            assert all_installed is False
            assert len(missing) == 4
            assert "pytest" in missing
            assert "build" in missing
            assert "twine" in missing
            assert "bump2version" in missing

    def test_verbose_mode(self, tmp_path, caplog):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            check_dependencies(tmp_path, venv_path, verbose=True)

            assert mock_find_spec.called

    def test_windows_paths(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / "Scripts"
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        with patch("sys.platform", "win32"):
            with patch("importlib.util.find_spec") as mock_find_spec:
                mock_find_spec.return_value = Mock()

                all_installed, missing = check_dependencies(
                    tmp_path, venv_path, verbose=False
                )

                assert all_installed is True


class TestVerifyDependencies:

    def test_verify_all_present(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        dependencies = ["pytest", "build", "twine", "bump2version"]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()

            all_verified, still_missing = verify_dependencies(
                tmp_path, venv_path, dependencies, verbose=False
            )

            assert all_verified is True
            assert still_missing == []

    def test_verify_missing_module(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        dependencies = ["pytest", "build"]

        def mock_find_spec(name):
            if name == "pytest":
                return None
            return Mock()

        with patch("importlib.util.find_spec", side_effect=mock_find_spec):
            all_verified, still_missing = verify_dependencies(
                tmp_path, venv_path, dependencies, verbose=False
            )

            assert all_verified is False
            assert "pytest" in still_missing

    def test_verify_missing_cli_tool_with_fallback(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        dependencies = ["bump2version"]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/local/bin/bump2version"

                all_verified, still_missing = verify_dependencies(
                    tmp_path, venv_path, dependencies, verbose=False
                )

                assert all_verified is True
                assert still_missing == []

    def test_verify_missing_cli_tool_no_fallback(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        dependencies = ["bump2version"]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None

                all_verified, still_missing = verify_dependencies(
                    tmp_path, venv_path, dependencies, verbose=False
                )

                assert all_verified is False
                assert "bump2version" in still_missing

    def test_verify_only_requested_deps(self, tmp_path):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        dependencies = ["pytest"]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            all_verified, still_missing = verify_dependencies(
                tmp_path, venv_path, dependencies, verbose=False
            )

            assert all_verified is False
            assert still_missing == ["pytest"]

    def test_verify_verbose_mode(self, tmp_path, caplog):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        dependencies = ["pytest"]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()

            verify_dependencies(tmp_path, venv_path, dependencies, verbose=True)

            assert mock_find_spec.called


class TestMain:

    def test_main_with_missing_deps(self, tmp_path, monkeypatch, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)

        monkeypatch.setenv("VENV_PATH", str(venv_path))

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            main()

            captured = capsys.readouterr()
            assert "pytest" in captured.out or "build" in captured.out

    def test_main_verbose_mode(self, tmp_path, monkeypatch, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        monkeypatch.setenv("VENV_PATH", str(venv_path))
        monkeypatch.setenv("MAESTRIA_VERBOSE", "1")

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()

            main()

            captured = capsys.readouterr()
            assert captured.out is not None

    def test_main_default_venv_path(self, tmp_path, capsys):
        venv_path = tmp_path / ".venv"
        venv_bin = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        venv_bin.mkdir(parents=True)
        (venv_bin / "bump2version").touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with patch("importlib.util.find_spec") as mock_find_spec:
                mock_find_spec.return_value = Mock()

                main()

            captured = capsys.readouterr()
            assert captured.out is not None
        finally:
            os.chdir(orig_cwd)
