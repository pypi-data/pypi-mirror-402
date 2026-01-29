"""Intercept Launcher - captures Hydra config metadata without running the task."""

import json
import sys
from typing import Any, List, Optional, Sequence

from hydra.core.config_store import ConfigStore
from hydra.core.global_hydra import GlobalHydra
from hydra.core.object_type import ObjectType
from hydra.core.utils import JobReturn
from hydra.plugins.launcher import Launcher
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig, OmegaConf

# Register the launcher config with Hydra using a plain dict
# This allows it to accept arbitrary fields when merged with other launcher configs
ConfigStore.instance().store(
    group="hydra/launcher",
    name="hydra_tui_inspector",
    node={
        "_target_": "hydra_plugins.hydra_intercept_launcher.launcher.InterceptLauncher",
    },
)


def get_all_groups(config_loader, parent: str = "") -> List[str]:
    """Recursively get all config groups that have options."""
    groups = []
    for group in config_loader.list_groups(parent):
        full_path = f"{parent}/{group}" if parent else group
        options = config_loader.get_group_options(full_path, ObjectType.CONFIG)
        if options:
            groups.append(full_path)
        # Recurse into subgroups
        groups.extend(get_all_groups(config_loader, full_path))
    return groups


class InterceptLauncher(Launcher):
    """Hydra launcher that intercepts config and prints metadata without running the task."""

    def __init__(self, **kwargs: Any) -> None:
        # Accept any kwargs to be compatible with other launcher configs
        self.config: Optional[DictConfig] = None
        self.task_function: Optional[TaskFunction] = None
        self.hydra_context: Optional[HydraContext] = None

    def setup(
        self,
        *,
        hydra_context: HydraContext,
        task_function: TaskFunction,
        config: DictConfig,
    ) -> None:
        """Setup the launcher with Hydra context and configuration."""
        self.config = config
        self.hydra_context = hydra_context
        self.task_function = task_function

    def launch(self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int) -> Sequence[JobReturn]:
        """
        Instead of launching jobs, extract and print config metadata.

        :param job_overrides: List of override lists (ignored)
        :param initial_job_idx: Initial job index (ignored)
        :return: Empty list (no jobs run)
        """
        assert self.config is not None
        assert self.hydra_context is not None

        # Get the config loader
        config_loader = GlobalHydra.instance().config_loader()

        # Get current choices from hydra.runtime.choices
        current_choices = dict(self.config.hydra.runtime.choices)

        # Get all config groups (excluding hydra internal groups)
        all_groups = get_all_groups(config_loader)
        all_groups = [g for g in all_groups if not g.startswith("hydra/")]

        # Build groups info
        groups_info = {}
        for group in sorted(all_groups):
            options = config_loader.get_group_options(group, ObjectType.CONFIG)
            groups_info[group] = {
                "options": sorted(options),
                "selected": current_choices.get(group),
            }

        # Build output
        # Convert OmegaConf DictConfig to dict without resolving interpolations
        config_dict = OmegaConf.to_container(self.config, resolve=False)

        output = {
            "groups": groups_info,
            "config": config_dict,
        }

        # Print JSON marker and data to stdout
        print("__HYDRA_INTERCEPT_START__")
        print(json.dumps(output, indent=2, default=str))
        print("__HYDRA_INTERCEPT_END__")

        # Exit without running the actual task
        sys.exit(0)
