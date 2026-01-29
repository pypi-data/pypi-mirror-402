# Copyright 2024-2025 eBay Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build command for Maestria."""

import os
import subprocess
from pathlib import Path
from typing import Any

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment

console = Console()


def build_project(config: Any) -> None:
    """Build the project.

    This uses Python's build module to create distribution packages.

    Args:
        config: Configuration object
    """
    project_dir = Path(config.root_dir)
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Step 1: Activate environment (done once at the beginning)
    try:
        env_info = activate_environment(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )
        python_path = env_info["python_path"]
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )
        return

    # Step 2: Run Python build
    console.print("[bold]Building project...[/bold]")
    try:
        result = run_in_environment(
            [str(python_path), "-m", "build", "--sdist", "--wheel"],
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=True,
            capture_output=True,
        )

        # Extract output filenames from the result
        output_files = []
        for line in result.stdout.split("\n"):
            if "dist/" in line and "RECORD" not in line:
                output_file = line.strip()
                if output_file:
                    output_files.append(output_file)

        console.print("[green]Project built successfully![/green]")

        if output_files:
            console.print("[bold]Built packages:[/bold]")
            for file in output_files:
                console.print(f"  - {file}")

        console.print(f"Distribution files available in {project_dir}/dist/")
    except (subprocess.CalledProcessError, RuntimeError, IOError, OSError) as e:
        console.print(f"[red]Failed to build project:[/red] {str(e)}")
        return
