"""Tests for the batch processing CLI commands."""

import os
import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from {{project_slug}}.cli import main


class TestBatchCommands:
    """Test the batch processing commands."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary JSON file with test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = Path(self.temp_dir) / "test_data.json"
        self.output_file = Path(self.temp_dir) / "output.json"
        
        # Sample data for testing
        self.test_data = [1, 2, 3, 4, 5]
        
        # Write test data to file
        with open(self.data_file, "w") as f:
            json.dump(self.test_data, f)
    
    def teardown_method(self):
        """Clean up after tests."""
        # Remove temporary files
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        os.rmdir(self.temp_dir)

    def test_batch_process_add(self):
        """Test batch process with add operation."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "batch", "process", 
            str(self.data_file),
            "--operation", "add",
            "--base", "10"
        ])
        
        assert result.exit_code == 0
        assert "Batch Results" in result.output
        for n in self.test_data:
            assert str(n) in result.output
            assert str(n + 10) in result.output

    def test_batch_process_subtract(self):
        """Test batch process with subtract operation."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "batch", "process", 
            str(self.data_file),
            "--operation", "subtract",
            "--base", "10"
        ])
        
        assert result.exit_code == 0
        assert "Batch Results" in result.output
        for n in self.test_data:
            assert str(n) in result.output
            assert str(10 - n) in result.output

    def test_batch_process_sum(self):
        """Test batch process with sum operation."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "batch", "process", 
            str(self.data_file),
            "--operation", "sum",
            "--base", "10"
        ])
        
        assert result.exit_code == 0
        assert "Batch Results" in result.output
        assert "Sum of all inputs" in result.output
        
        # Sum of test_data + base
        expected_sum = sum(self.test_data) + 10
        assert str(expected_sum) in result.output

    def test_batch_process_with_output(self):
        """Test batch process with output file."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "batch", "process", 
            str(self.data_file),
            "--operation", "add",
            "--base", "10",
            "--output", str(self.output_file)
        ])
        
        assert result.exit_code == 0
        assert f"Results saved to {self.output_file}" in result.output
        
        # Verify the output file was created and contains the expected data
        assert os.path.exists(self.output_file)
        
        with open(self.output_file, "r") as f:
            output_data = json.load(f)
            
        assert isinstance(output_data, list)
        assert len(output_data) == len(self.test_data)
        
        for i, n in enumerate(self.test_data):
            assert output_data[i] == n + 10

    def test_batch_process_invalid_file(self):
        """Test batch process with invalid file."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "batch", "process", 
            "nonexistent_file.json",
            "--operation", "add",
            "--base", "10"
        ])
        
        assert result.exit_code != 0  # Should fail with nonexistent file

    def test_batch_process_invalid_json(self):
        """Test batch process with invalid JSON file."""
        # Create a file with invalid JSON
        invalid_json_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("This is not valid JSON")
            
        try:
            runner = CliRunner()
            result = runner.invoke(main, [
                "batch", "process", 
                str(invalid_json_file),
                "--operation", "add",
                "--base", "10"
            ])
            
            assert result.exit_code == 0  # Command handles error gracefully
            assert "Invalid JSON file" in result.output
        finally:
            if os.path.exists(invalid_json_file):
                os.remove(invalid_json_file)