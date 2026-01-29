"""Tests for the Maestria plugin system."""

from typing import Callable, Dict, List
from unittest.mock import Mock, patch

from maestria.plugins import (
    MaestriaPlugin,
    discover_plugins,
    get_plugin_commands,
    get_plugin_hooks,
    run_hook,
)


class TestPlugin(MaestriaPlugin):
    """Test plugin for testing."""

    name = "test-plugin"
    description = "A test plugin"

    @classmethod
    def get_commands(cls) -> Dict[str, Callable]:
        def test_command():
            return "test"

        return {"test-cmd": test_command}

    @classmethod
    def get_hooks(cls) -> Dict[str, List[Callable]]:
        def test_hook():
            return "hook_result"

        return {"pre_command": [test_hook]}

    @classmethod
    def initialize(cls) -> None:
        pass


class TestMaestriaPlugin:
    """Tests for MaestriaPlugin base class."""

    def test_base_plugin_name(self):
        """Test base plugin has default name."""
        assert MaestriaPlugin.name == "base"

    def test_base_plugin_description(self):
        """Test base plugin has default description."""
        assert MaestriaPlugin.description == "Base plugin"

    def test_base_plugin_get_commands(self):
        """Test base plugin returns empty commands."""
        assert MaestriaPlugin.get_commands() == {}

    def test_base_plugin_get_hooks(self):
        """Test base plugin returns empty hooks."""
        assert MaestriaPlugin.get_hooks() == {}

    def test_base_plugin_initialize(self):
        """Test base plugin initialize does nothing."""
        MaestriaPlugin.initialize()


class TestDiscoverPlugins:
    """Tests for discover_plugins function."""

    def setup_method(self):
        """Reset plugin cache before each test."""
        import maestria.plugins

        maestria.plugins._plugins = {}
        maestria.plugins._commands = {}
        maestria.plugins._hooks = {}

    @patch("importlib.metadata.entry_points")
    def test_discover_plugins_no_plugins(self, mock_entry_points):
        """Test discovering plugins when none are installed."""
        mock_entry_points.return_value = []

        plugins = discover_plugins()
        assert plugins == {}

    @patch("importlib.metadata.entry_points")
    @patch("maestria.plugins.console")
    def test_discover_plugins_with_plugin(self, mock_console, mock_entry_points):
        """Test discovering installed plugins."""
        mock_ep = Mock()
        mock_ep.name = "test-plugin"
        mock_ep.load = Mock(return_value=TestPlugin)

        mock_entry_points.return_value = [mock_ep]

        plugins = discover_plugins()
        assert "test-plugin" in plugins
        assert plugins["test-plugin"] == TestPlugin
        mock_console.print.assert_called()

    @patch("importlib.metadata.entry_points")
    @patch("maestria.plugins.console")
    def test_discover_plugins_caching(self, mock_console, mock_entry_points):
        """Test that plugins are cached after first discovery."""
        mock_ep = Mock()
        mock_ep.name = "test-plugin"
        mock_ep.load = Mock(return_value=TestPlugin)
        mock_entry_points.return_value = [mock_ep]

        plugins1 = discover_plugins()
        plugins2 = discover_plugins()

        assert plugins1 == plugins2
        mock_entry_points.assert_called_once()

    @patch("importlib.metadata.entry_points")
    @patch("maestria.plugins.console")
    def test_discover_plugins_load_error(self, mock_console, mock_entry_points):
        """Test handling plugin load errors."""
        mock_ep = Mock()
        mock_ep.name = "broken-plugin"
        mock_ep.load = Mock(side_effect=Exception("Load failed"))

        mock_entry_points.return_value = [mock_ep]

        plugins = discover_plugins()
        assert "broken-plugin" not in plugins
        assert any(
            "Error loading plugin" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("importlib.metadata.entry_points")
    @patch("maestria.plugins.console")
    def test_discover_plugins_initialize_error(self, mock_console, mock_entry_points):
        """Test handling plugin initialization errors."""

        class BrokenPlugin(MaestriaPlugin):
            name = "broken"

            @classmethod
            def initialize(cls):
                raise Exception("Init failed")

        mock_ep = Mock()
        mock_ep.name = "broken"
        mock_ep.load = Mock(return_value=BrokenPlugin)
        mock_entry_points.return_value = [mock_ep]

        plugins = discover_plugins()
        assert "broken" in plugins
        assert any(
            "Error initializing plugin" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("importlib.metadata.entry_points", side_effect=TypeError)
    def test_discover_plugins_python39_fallback(self, mock_entry_points):
        """Test fallback for Python 3.8-3.9."""
        with patch("importlib.metadata.entry_points") as mock_all_eps:
            mock_ep = Mock()
            mock_ep.name = "test"
            mock_ep.group = "maestria.plugins"
            mock_ep.load = Mock(return_value=TestPlugin)

            mock_all_eps.return_value = [mock_ep]

            plugins = discover_plugins()
            assert "test" in plugins


class TestGetPluginCommands:
    """Tests for get_plugin_commands function."""

    def setup_method(self):
        """Reset plugin cache before each test."""
        import maestria.plugins

        maestria.plugins._plugins = {}
        maestria.plugins._commands = {}
        maestria.plugins._hooks = {}

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_commands_no_plugins(self, mock_discover):
        """Test getting commands when no plugins."""
        mock_discover.return_value = {}

        commands = get_plugin_commands()
        assert commands == {}

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_commands_with_commands(self, mock_discover):
        """Test getting commands from plugins."""
        mock_discover.return_value = {"test-plugin": TestPlugin}

        commands = get_plugin_commands()
        assert "test-cmd" in commands
        assert commands["test-cmd"]() == "test"

    @patch("maestria.plugins.discover_plugins")
    @patch("maestria.plugins.console")
    def test_get_plugin_commands_duplicate_warning(self, mock_console, mock_discover):
        """Test warning for duplicate command names."""

        class Plugin2(MaestriaPlugin):
            @classmethod
            def get_commands(cls):
                return {"test-cmd": lambda: "override"}

        mock_discover.return_value = {
            "plugin1": TestPlugin,
            "plugin2": Plugin2,
        }

        commands = get_plugin_commands()
        assert "test-cmd" in commands
        assert any(
            "overrides an existing command" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.plugins.discover_plugins")
    @patch("maestria.plugins.console")
    def test_get_plugin_commands_error(self, mock_console, mock_discover):
        """Test handling errors getting commands."""

        class BrokenPlugin(MaestriaPlugin):
            @classmethod
            def get_commands(cls):
                raise Exception("Commands error")

        mock_discover.return_value = {"broken": BrokenPlugin}

        commands = get_plugin_commands()
        assert commands == {}
        assert any(
            "Error getting commands" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_commands_caching(self, mock_discover):
        """Test that commands are cached."""
        mock_discover.return_value = {"test-plugin": TestPlugin}

        commands1 = get_plugin_commands()
        commands2 = get_plugin_commands()

        assert commands1 == commands2
        mock_discover.assert_called_once()


class TestGetPluginHooks:
    """Tests for get_plugin_hooks function."""

    def setup_method(self):
        """Reset plugin cache before each test."""
        import maestria.plugins

        maestria.plugins._plugins = {}
        maestria.plugins._commands = {}
        maestria.plugins._hooks = {}

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_hooks_no_plugins(self, mock_discover):
        """Test getting hooks when no plugins."""
        mock_discover.return_value = {}

        hooks = get_plugin_hooks()
        assert hooks == {}

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_hooks_with_hooks(self, mock_discover):
        """Test getting hooks from plugins."""
        mock_discover.return_value = {"test-plugin": TestPlugin}

        hooks = get_plugin_hooks()
        assert "pre_command" in hooks
        assert len(hooks["pre_command"]) == 1
        assert hooks["pre_command"][0]() == "hook_result"

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_hooks_single_function(self, mock_discover):
        """Test handling hooks that are single functions not lists."""

        class Plugin(MaestriaPlugin):
            @classmethod
            def get_hooks(cls):
                def single_hook():
                    return "single"

                return {"test_hook": single_hook}

        mock_discover.return_value = {"plugin": Plugin}

        hooks = get_plugin_hooks()
        assert "test_hook" in hooks
        assert isinstance(hooks["test_hook"], list)
        assert len(hooks["test_hook"]) == 1

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_hooks_multiple_plugins(self, mock_discover):
        """Test merging hooks from multiple plugins."""

        class Plugin2(MaestriaPlugin):
            @classmethod
            def get_hooks(cls):
                def hook2():
                    return "hook2"

                return {"pre_command": [hook2]}

        mock_discover.return_value = {
            "plugin1": TestPlugin,
            "plugin2": Plugin2,
        }

        hooks = get_plugin_hooks()
        assert "pre_command" in hooks
        assert len(hooks["pre_command"]) == 2

    @patch("maestria.plugins.discover_plugins")
    @patch("maestria.plugins.console")
    def test_get_plugin_hooks_error(self, mock_console, mock_discover):
        """Test handling errors getting hooks."""

        class BrokenPlugin(MaestriaPlugin):
            @classmethod
            def get_hooks(cls):
                raise Exception("Hooks error")

        mock_discover.return_value = {"broken": BrokenPlugin}

        hooks = get_plugin_hooks()
        assert hooks == {}
        assert any(
            "Error getting hooks" in str(call)
            for call in mock_console.print.call_args_list
        )

    @patch("maestria.plugins.discover_plugins")
    def test_get_plugin_hooks_caching(self, mock_discover):
        """Test that hooks are cached."""
        mock_discover.return_value = {"test-plugin": TestPlugin}

        hooks1 = get_plugin_hooks()
        hooks2 = get_plugin_hooks()

        assert hooks1 == hooks2
        mock_discover.assert_called_once()


class TestRunHook:
    """Tests for run_hook function."""

    def setup_method(self):
        """Reset plugin cache before each test."""
        import maestria.plugins

        maestria.plugins._plugins = {}
        maestria.plugins._commands = {}
        maestria.plugins._hooks = {}

    @patch("maestria.plugins.get_plugin_hooks")
    def test_run_hook_no_hooks(self, mock_get_hooks):
        """Test running hook when none exist."""
        mock_get_hooks.return_value = {}

        results = run_hook("nonexistent_hook")
        assert results == []

    @patch("maestria.plugins.get_plugin_hooks")
    def test_run_hook_with_results(self, mock_get_hooks):
        """Test running hook and collecting results."""

        def hook1():
            return "result1"

        def hook2():
            return "result2"

        mock_get_hooks.return_value = {"test_hook": [hook1, hook2]}

        results = run_hook("test_hook")
        assert len(results) == 2
        assert "result1" in results
        assert "result2" in results

    @patch("maestria.plugins.get_plugin_hooks")
    def test_run_hook_with_args(self, mock_get_hooks):
        """Test running hook with arguments."""

        def hook(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        mock_get_hooks.return_value = {"test_hook": [hook]}

        results = run_hook("test_hook", "a", "b", kwarg1="c")
        assert results == ["a-b-c"]

    @patch("maestria.plugins.get_plugin_hooks")
    @patch("maestria.plugins.console")
    def test_run_hook_error_handling(self, mock_console, mock_get_hooks):
        """Test handling hook execution errors."""

        def broken_hook():
            raise Exception("Hook failed")

        def working_hook():
            return "success"

        mock_get_hooks.return_value = {"test_hook": [broken_hook, working_hook]}

        results = run_hook("test_hook")
        assert len(results) == 1
        assert "success" in results
        assert any(
            "Error running hook" in str(call)
            for call in mock_console.print.call_args_list
        )
