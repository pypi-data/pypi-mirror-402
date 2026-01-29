"""CLI entry point for hydra-tui."""

import json
import re
import subprocess
import sys
from typing import Any, Optional

from rich.console import Console

from .tui.app import run_tui
from .tui.models import ConfigGroup, ConfigValue, HydraConfig

# Hydra flags that take a value (need to capture the next argument too)
HYDRA_FLAGS_WITH_VALUE = {
    "-cn",
    "--config-name",
    "-cp",
    "--config-path",
    "-cd",
    "--config-dir",
    "-p",
    "--package",
    "--experimental-rerun",
    "--cfg",  # --cfg {job,hydra,all}
    "--info",  # --info [{all,config,defaults,defaults-tree,plugins,searchpath}]
}

# Hydra flags that are standalone (no value)
HYDRA_FLAGS_STANDALONE = {
    "--help",
    "-h",
    "--hydra-help",
    "--version",
    "--resolve",
    "--run",
    "--multirun",
    "-m",
    "--shell-completion",
}

# Pattern to detect Hydra overrides: key=value, +key=value, ++key=value, ~key
OVERRIDE_PATTERN = re.compile(r"^(\+\+?|~)?[\w./@]+[=]|^~[\w./@]+$")


def is_hydra_override(arg: str) -> bool:
    """Check if an argument is a Hydra override."""
    return bool(OVERRIDE_PATTERN.match(arg))


def separate_command_parts(args: list[str]) -> tuple[list[str], list[str]]:
    """Separate command into base+flags and user overrides.

    Returns:
        (base_command_with_flags, user_overrides)

    Hydra flags like -cn, --config-path are kept in base command.
    User overrides (key=value, +key=value, ~key) are separated.
    """
    base_command: list[str] = []
    user_overrides: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]

        # Check if it's a Hydra flag with a value
        if arg in HYDRA_FLAGS_WITH_VALUE:
            base_command.append(arg)
            # Also capture the next argument (the value)
            if i + 1 < len(args):
                i += 1
                base_command.append(args[i])
        # Check if it's a standalone Hydra flag
        elif arg in HYDRA_FLAGS_STANDALONE:
            base_command.append(arg)
        # Check if it's a Hydra override
        elif is_hydra_override(arg):
            user_overrides.append(arg)
        # Otherwise it's part of the base command (program name, etc.)
        else:
            base_command.append(arg)

        i += 1

    return base_command, user_overrides


def run_intercept(command: list[str]) -> tuple[Optional[dict], str]:
    """Run the intercept command and parse the output.

    Returns:
        (parsed_data, raw_output) - parsed_data is None if parsing failed
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    # Combine stdout and stderr (Hydra may print to either)
    output = result.stdout + result.stderr

    return parse_intercept_output(output), output


def extract_hydra_error(output: str) -> str | None:
    """Extract a user-friendly error message from Hydra output.

    Looks for common Hydra error patterns and returns a clean message.
    Returns None if no recognizable error pattern found.
    """
    # Look for ConfigCompositionException (override errors)
    if "ConfigCompositionException:" in output:
        # Find the line with the actual error message
        for line in output.split("\n"):
            if "ConfigCompositionException:" in line:
                # Extract everything after the exception name
                msg = line.split("ConfigCompositionException:")[-1].strip()
                return msg
            # Also capture the "To append" hint if present
            if "To append to your config use" in line:
                return line.strip()

    # Look for ConfigAttributeError (key not found)
    if "ConfigAttributeError:" in output:
        for line in output.split("\n"):
            if "ConfigAttributeError:" in line:
                msg = line.split("ConfigAttributeError:")[-1].strip()
                return msg

    # Look for generic Hydra errors
    if "hydra.errors." in output:
        for line in output.split("\n"):
            if "hydra.errors." in line and ":" in line:
                # Extract the error type and message
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()

    # Look for OmegaConf errors
    if "omegaconf.errors." in output:
        for line in output.split("\n"):
            if "omegaconf.errors." in line and ":" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()

    return None


def parse_intercept_output(output: str) -> Optional[dict]:
    """Parse the JSON output from the intercept launcher."""
    start_marker = "__HYDRA_INTERCEPT_START__"
    end_marker = "__HYDRA_INTERCEPT_END__"

    start_idx = output.find(start_marker)
    end_idx = output.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        return None

    json_str = output[start_idx + len(start_marker) : end_idx].strip()
    return json.loads(json_str)


def flatten_config(config: dict, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested config into dot-notation paths."""
    flattened = {}

    if isinstance(config, dict):
        for key, value in config.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)) and value:
                flattened.update(flatten_config(value, new_key))
            else:
                flattened[new_key] = value
    elif isinstance(config, list):
        for i, value in enumerate(config):
            new_key = f"{prefix}.{i}"
            if isinstance(value, (dict, list)) and value:
                flattened.update(flatten_config(value, new_key))
            else:
                flattened[new_key] = value
    else:
        flattened[prefix] = config

    return flattened


def build_hydra_config_from_diff(
    baseline_data: dict,
    modified_data: dict,
    command: list[str],
) -> HydraConfig:
    """Build HydraConfig by comparing baseline and modified configs.

    Args:
        baseline_data: Config data WITHOUT user overrides (the defaults)
        modified_data: Config data WITH user overrides applied
        command: Base command (without user overrides)

    The diff determines what's modified:
    - Same value in both: not modified (original_value = value)
    - Different value: modified (original_value from baseline, value from modified)
    - Only in modified: NEW from +key=value (original_value = None)
    - Only in baseline: DELETED from ~key (value = None)
    """
    baseline_groups = baseline_data.get("groups", {})
    modified_groups = modified_data.get("groups", {})
    baseline_config = baseline_data.get("config", {})
    modified_config = modified_data.get("config", {})

    # Build config groups by comparing baseline and modified
    groups = {}
    all_group_names = set(baseline_groups.keys()) | set(modified_groups.keys())

    for group_name in all_group_names:
        # Skip hydra internal groups
        if group_name.startswith("hydra"):
            continue

        baseline_info = baseline_groups.get(group_name, {})
        modified_info = modified_groups.get(group_name, {})

        # Use modified options if available, else baseline
        options = modified_info.get("options", baseline_info.get("options", []))
        baseline_selected = baseline_info.get("selected")
        modified_selected = modified_info.get("selected")

        # Determine current selection (from modified) and original (from baseline)
        selected = [modified_selected] if modified_selected else []
        original_selected = baseline_selected

        groups[group_name] = ConfigGroup(
            name=group_name,
            options=options,
            selected=selected,
            original_selected=original_selected,
            multirun=False,
        )

    # Build config values by comparing flattened baseline and modified
    baseline_without_hydra = {k: v for k, v in baseline_config.items() if k != "hydra"}
    modified_without_hydra = {k: v for k, v in modified_config.items() if k != "hydra"}

    baseline_flat = flatten_config(baseline_without_hydra)
    modified_flat = flatten_config(modified_without_hydra)

    all_paths = set(baseline_flat.keys()) | set(modified_flat.keys())

    values = {}
    for path in all_paths:
        baseline_value = baseline_flat.get(path)
        modified_value = modified_flat.get(path)

        if path in baseline_flat and path in modified_flat:
            # Key exists in both - use baseline as original, modified as current
            values[path] = ConfigValue(
                path=path,
                value=modified_value,
                original_value=baseline_value,
            )
        elif path in modified_flat:
            # Key only in modified - NEW (from +key=value)
            values[path] = ConfigValue(
                path=path,
                value=modified_value,
                original_value=None,  # Marks as NEW
            )
        else:
            # Key only in baseline - DELETED (from ~key)
            values[path] = ConfigValue(
                path=path,
                value=None,  # Marks as deleted
                original_value=baseline_value,
            )

    return HydraConfig(groups=groups, values=values, command=command)


def main() -> None:
    """Main entry point for hydra-tui CLI."""
    console = Console()

    if len(sys.argv) < 2:
        console.print("[bold cyan]Hydra TUI[/bold cyan] - Interactive Hydra Configuration")
        console.print()
        console.print("[bold]Usage:[/bold] hydra-tui <command>")
        console.print("[dim]Example: hydra-tui uv run jetrl-router[/dim]")
        sys.exit(1)

    # Get the command to intercept
    command = sys.argv[1:]

    # Separate base command (with Hydra flags) from user overrides
    base_command, cli_overrides = separate_command_parts(command)

    # Build intercept command: insert -m hydra/launcher=... right after program name
    # to avoid argument ordering issues with Hydra
    baseline_cmd = [base_command[0], "-m", "hydra/launcher=hydra_tui_inspector"] + base_command[1:]

    try:
        # Run intercept #1: WITHOUT user overrides (baseline config)
        with console.status("[bold cyan]Loading configuration...[/bold cyan]", spinner="dots"):
            baseline_data, baseline_output = run_intercept(baseline_cmd)

            if baseline_data is None:
                console.print("[bold red]Error:[/bold red] Failed to load configuration.")
                error_msg = extract_hydra_error(baseline_output)
                if error_msg:
                    console.print(f"[yellow]{error_msg}[/yellow]")
                else:
                    console.print("[dim]Command output:[/dim]")
                    console.print(baseline_output)
                sys.exit(1)

            # Run intercept #2: WITH user overrides (if any)
            if cli_overrides:
                modified_cmd = (
                    [base_command[0], "-m", "hydra/launcher=hydra_tui_inspector"] + base_command[1:] + cli_overrides
                )
                modified_data, modified_output = run_intercept(modified_cmd)

                if modified_data is None:
                    console.print("[bold red]Error:[/bold red] Invalid override.")
                    error_msg = extract_hydra_error(modified_output)
                    if error_msg:
                        console.print(f"[yellow]{error_msg}[/yellow]")
                    else:
                        console.print("[dim]Command output:[/dim]")
                        console.print(modified_output)
                    sys.exit(1)
            else:
                # No overrides - modified is same as baseline
                modified_data = baseline_data

        # Build config by diffing baseline and modified
        # Type assertions - we've already checked for None above
        assert baseline_data is not None
        assert modified_data is not None
        config = build_hydra_config_from_diff(baseline_data, modified_data, base_command)

        # Launch TUI
        should_execute, overrides = run_tui(config)

        if should_execute:
            # Build final command with overrides
            # Use base_command (without CLI overrides) since overrides come from TUI
            final_command = list(base_command)

            # Add -m flag if multirun is active and not already present
            multirun_count = config.get_multirun_count()
            if multirun_count:
                # Check if -m or --multirun is already in the command
                if "-m" not in final_command and "--multirun" not in final_command:
                    final_command.append("-m")

            final_command.extend(overrides)

            # Show beautiful command display
            console.print()
            console.print("─" * console.width)

            if multirun_count and multirun_count > 1:
                console.print(f"[bold green]🚀 Launching {multirun_count} experiments[/bold green]")
            else:
                console.print("[bold green]🚀 Running command[/bold green]")

            console.print()

            # Show command with syntax highlighting
            cmd_str = " ".join(final_command)
            # Highlight overrides in the command
            for override in overrides:
                if override.startswith("~"):
                    # Deletion (red)
                    cmd_str = cmd_str.replace(override, f"[red]{override}[/red]")
                elif override.startswith("+"):
                    # New config group (green)
                    cmd_str = cmd_str.replace(override, f"[green]{override}[/green]")
                else:
                    # Regular override (yellow)
                    cmd_str = cmd_str.replace(override, f"[yellow]{override}[/yellow]")

            # Highlight the -m flag if present and we're in multirun mode
            if multirun_count and multirun_count > 1:
                if " -m " in cmd_str:
                    cmd_str = cmd_str.replace(" -m ", " [magenta]-m[/magenta] ", 1)
                elif " --multirun " in cmd_str:
                    cmd_str = cmd_str.replace(" --multirun ", " [magenta]--multirun[/magenta] ", 1)

            console.print(f"  [bold cyan]$[/bold cyan] {cmd_str}")
            console.print()
            console.print("─" * console.width)
            console.print()

            # Execute the command (stdout/stderr will appear naturally)
            subprocess.run(final_command, check=False)
        else:
            console.print("\n[yellow]Cancelled[/yellow]")

    except FileNotFoundError:
        console.print(f"[bold red]✗ Error:[/bold red] Command not found: {command[0]}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]✗ Error:[/bold red] Failed to parse configuration: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
