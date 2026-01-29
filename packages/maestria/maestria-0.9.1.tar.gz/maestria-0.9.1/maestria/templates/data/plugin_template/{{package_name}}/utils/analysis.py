"""Project analysis utilities for the {{plugin_name}} plugin."""

import os
from pathlib import Path
from typing import Dict, Any, List


def count_files_by_extension(directory: Path) -> Dict[str, int]:
    """Count the number of files by extension in a directory.

    Args:
        directory: Directory to analyze

    Returns:
        Dictionary mapping file extensions to counts
    """
    extension_counts: Dict[str, int] = {}

    for root, _, files in os.walk(directory):
        for file in files:
            # Skip hidden files
            if file.startswith("."):
                continue

            # Get file extension
            _, ext = os.path.splitext(file)
            ext = ext.lower()

            # Count extension
            if ext:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
            else:
                extension_counts["(no extension)"] = (
                    extension_counts.get("(no extension)", 0) + 1
                )

    return extension_counts


def count_lines_of_code(
    directory: Path, extensions: List[str] = [".py", ".pyx", ".pyd"]
) -> int:
    """Count the total lines of code in a directory.

    Args:
        directory: Directory to analyze
        extensions: List of file extensions to count (default: [".py", ".pyx", ".pyd"])

    Returns:
        Total lines of code
    """
    total_lines = 0

    for root, _, files in os.walk(directory):
        for file in files:
            # Skip hidden files
            if file.startswith("."):
                continue

            # Check if file has the right extension
            _, ext = os.path.splitext(file)
            if ext.lower() not in extensions:
                continue

            # Count lines in the file
            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    total_lines += sum(1 for _ in f)
            except (UnicodeDecodeError, PermissionError, IOError):
                # Skip files that can't be read
                continue

    return total_lines


def analyze_project(directory: Path) -> Dict[str, Any]:
    """Analyze a Python project.

    Args:
        directory: Directory to analyze

    Returns:
        Dictionary of analysis results
    """
    results: Dict[str, Any] = {}

    # Get basic statistics
    results["Total files"] = sum(len(files) for _, _, files in os.walk(directory))
    results["Total directories"] = sum(len(dirs) for _, dirs, _ in os.walk(directory))

    # Count files by extension
    extension_counts = count_files_by_extension(directory)
    for ext, count in sorted(
        extension_counts.items(), key=lambda x: x[1], reverse=True
    ):
        results[f"Files {ext}"] = count

    # Count lines of code
    results["Python lines of code"] = count_lines_of_code(directory)

    # Check for common project files
    common_files = [
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Makefile",
        "Dockerfile",
    ]
    for file in common_files:
        results[f"Has {file}"] = os.path.exists(os.path.join(directory, file))

    return results
