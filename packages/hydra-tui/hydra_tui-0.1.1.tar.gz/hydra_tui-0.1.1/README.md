# Hydra TUI

Interactive terminal UI for exploring and configuring Hydra-based applications.

## Overview

Hydra TUI provides a visual interface to discover config groups, select options, and build override commands—no need to memorize config names or dig through YAML files.

## Quick Start

Install as a development dependency in your Hydra project:

```bash
uv add --dev git+https://github.com/JetBrains-Research/hydra-tui
```

> **Note:** `uv tool install` will not work for this package. Hydra TUI includes a Hydra plugin that must be installed in the same Python environment as your Hydra application.

### Running the TUI

Wrap any Hydra command with `hydra-tui`:

```bash
# Instead of:
python my_app.py

# Use:
source .venv/bin/activate
hydra-tui python my_app.py
# or with uv:
uv run hydra-tui python my_app.py
```

The TUI will:
1. Load all available config groups and values
2. Let you interactively select/modify configurations
3. Execute your command with the chosen overrides

## Interface

### Config Groups
- **Enter**: Select single option
- **Spacebar**: Toggle multiple options (multirun)
- **⚡**: Indicates multirun mode

### Config Values
- **Enter**: Edit value inline

### Running
- **r**: Show confirmation and run
- **Ctrl+C**: Quit
