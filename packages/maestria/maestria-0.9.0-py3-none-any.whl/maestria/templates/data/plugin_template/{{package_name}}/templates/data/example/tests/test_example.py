"""Tests for the example project."""

import pytest
from click.testing import CliRunner

from example.__main__ import main


def test_main():
    """Test the main CLI function."""
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "Example project" in result.output
    assert "{{plugin_name}}" in result.output
