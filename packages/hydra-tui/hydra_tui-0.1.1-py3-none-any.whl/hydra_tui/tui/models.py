"""Data models for Hydra configuration."""

import re
import shlex
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ConfigGroup:
    """Represents a config group with selectable options."""

    name: str
    options: list[str]
    selected: list[str] = field(default_factory=list)  # Can be multiple for multirun
    original_selected: str | None = None  # What was originally selected
    multirun: bool = False

    def get_display_value(self) -> str:
        """Get the display string for current selection."""
        if not self.selected:
            return "not set"
        if len(self.selected) == 1:
            return self.selected[0]
        return ", ".join(self.selected)

    def is_modified(self) -> bool:
        """Check if this group has been modified from original."""
        if not self.selected and not self.original_selected:
            return False
        if len(self.selected) == 1 and self.selected[0] == self.original_selected:
            return False
        return True


@dataclass
class ConfigValue:
    """Represents an individual config value."""

    path: str  # e.g., "actor_rollout_ref.rollout.trace.backend"
    value: Any
    original_value: Any

    def is_modified(self) -> bool:
        """Check if this value has been modified."""
        return self.value != self.original_value

    def get_display_value(self) -> str:
        """Get the display string for the value."""
        # Use YAML serialization to properly handle all types
        # (None -> null, booleans -> true/false, lists, dicts, etc.)
        value_str = yaml.dump(self.value, default_flow_style=True, width=float("inf")).strip()

        # Remove trailing ... that yaml adds for documents
        if value_str.endswith("..."):
            value_str = value_str[:-3].strip()

        if len(value_str) > 60:
            return value_str[:57] + "..."
        return value_str


@dataclass
class HydraConfig:
    """Container for all Hydra configuration data."""

    groups: dict[str, ConfigGroup]
    values: dict[str, ConfigValue]
    command: list[str]  # The base command to run

    def _needs_escaping(self, value: str) -> bool:
        """Check if a value needs shell escaping."""
        # Check if value contains spaces or special shell characters
        return bool(re.search(r'[\s\'"\\$`!*?(){}[\]<>|;&]', str(value)))

    def _escape_if_needed(self, value: Any) -> str:
        """Escape value only if it needs escaping."""
        # Use YAML serialization to properly handle all types
        # This ensures compatibility with Hydra's YAML-based override parsing
        value_str = yaml.dump(value, default_flow_style=True, width=float("inf")).strip()

        # Remove trailing ... that yaml adds for documents
        if value_str.endswith("..."):
            value_str = value_str[:-3].strip()

        if self._needs_escaping(value_str):
            return shlex.quote(value_str)
        return value_str

    def get_overrides(self) -> list[str]:
        """Generate list of override strings for modified values.

        Config groups use:
        - group=value (if originally set)
        - +group=value (if originally not set)
        - ~group (if deleting)

        Config values use:
        - key=value (no prefix)
        """
        overrides = []

        # Add config group overrides
        for group in self.groups.values():
            if group.is_modified():
                if not group.selected and group.original_selected:
                    # Delete: use ~ syntax
                    overrides.append(f"~{group.name}")
                elif group.multirun:
                    # Multi-run: join with comma, escape each value if needed
                    values = [self._escape_if_needed(v) for v in group.selected]
                    value = ",".join(values)
                    # Use + if originally not set, no prefix if originally set
                    prefix = "+" if not group.original_selected else ""
                    overrides.append(f"{prefix}{group.name}={value}")
                else:
                    # Single value
                    if group.selected:
                        value = self._escape_if_needed(group.selected[0])
                        # Use + if originally not set, no prefix if originally set
                        prefix = "+" if not group.original_selected else ""
                        overrides.append(f"{prefix}{group.name}={value}")

        # Add config value overrides (no prefix needed)
        for config_value in self.values.values():
            if config_value.is_modified():
                value = self._escape_if_needed(config_value.value)
                overrides.append(f"{config_value.path}={value}")

        return overrides

    def get_modified_count(self) -> int:
        """Count how many modifications have been made."""
        return sum(1 for g in self.groups.values() if g.is_modified()) + sum(
            1 for v in self.values.values() if v.is_modified()
        )

    def get_multirun_count(self) -> int | None:
        """Calculate number of experiments for multirun (cartesian product).

        Returns None if no multirun groups, otherwise returns the product.
        """
        multirun_groups = [g for g in self.groups.values() if g.multirun and g.selected]

        if not multirun_groups:
            return None

        # Calculate cartesian product
        count = 1
        for group in multirun_groups:
            count *= len(group.selected)

        return count
