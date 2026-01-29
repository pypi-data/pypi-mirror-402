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

"""Run command for Maestria."""

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, List, Optional

from rich.console import Console

from maestria.environment import activate_environment, run_in_environment

console = Console()


def run_script(
    config: Any,
    script: str,
    args: Optional[List[str]] = None,
) -> None:
    """Run a script defined in pyproject.toml.

    This executes scripts defined in pyproject.toml directly.

    Args:
        config: Configuration object
        script: The name of the script to run
        args: Additional arguments to pass to the script
    """
    project_dir = Path(config.root_dir)
    scripts = config.scripts
    verbose = os.environ.get("MAESTRIA_VERBOSE") == "1"

    # Step 1: Check if the script exists
    if not scripts or script not in scripts:
        console.print(f"[yellow]Script '{script}' not found in pyproject.toml[/yellow]")
        console.print("Available scripts:")
        if scripts:
            for script_name, script_cmd in scripts.items():
                if isinstance(script_cmd, dict) and "cmd" in script_cmd:
                    console.print(f"  - {script_name}: {script_cmd['cmd']}")
                else:
                    console.print(f"  - {script_name}: {script_cmd}")
        else:
            console.print("  No scripts defined in pyproject.toml")
        console.print("\nUse 'python -m <module>' to run a Python module directly.")
        return

    # Get the script command
    script_cmd = scripts[script]

    # Step 2: Activate environment (done once at the beginning)
    try:
        env_info = activate_environment(
            project_dir, venv_path=config.venv_path, verbose=verbose
        )
        python_path = env_info["python_path"]
        venv_bin_path = os.path.dirname(python_path)
    except RuntimeError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )
        return

    # Step 3: Prepare the command
    # Split the command into executable and args
    if isinstance(script_cmd, str):
        cmd_parts = shlex.split(script_cmd)
    else:
        cmd_parts = [script_cmd]

    # Check if it's a Python module or a command
    if cmd_parts[0] in ["python", "python3", "py"]:
        # Replace with venv python
        cmd = [str(python_path)] + cmd_parts[1:]
    elif os.path.exists(os.path.join(venv_bin_path, cmd_parts[0])):
        # Use the command from the venv
        cmd = [os.path.join(venv_bin_path, cmd_parts[0])] + cmd_parts[1:]
    else:
        # Use the command as is, with Python from venv
        cmd = [str(python_path), "-m"] + cmd_parts

    # Add any additional arguments
    if args:
        cmd.extend(args)

    # Step 4: Run the script
    console.print(f"[bold]Running script: {script}[/bold]")
    try:
        run_in_environment(
            cmd,
            project_dir,
            venv_path=config.venv_path,
            verbose=verbose,
            check=False,  # Don't raise an exception if the script fails
            capture_output=False,  # Show output directly
        )
    except (subprocess.CalledProcessError, RuntimeError, IOError, OSError) as e:
        console.print(f"[red]Error running script: {str(e)}[/red]")
        console.print(
            "Make sure you have run 'maestria env setup' to set up your environment."
        )
