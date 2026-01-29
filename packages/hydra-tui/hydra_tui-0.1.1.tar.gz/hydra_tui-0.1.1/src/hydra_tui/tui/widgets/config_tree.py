"""Config tree widget for displaying and navigating Hydra configuration."""

from textual import events
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ..models import HydraConfig


class ConfigGroupTree(Tree[str]):
    """Tree widget for displaying config groups."""

    class OptionSelected(Message):
        """Posted when an option is selected with Enter or Space."""

        def __init__(self, group_name: str, option_name: str, is_multirun: bool) -> None:
            super().__init__()
            self.group_name = group_name
            self.option_name = option_name
            self.is_multirun = is_multirun

    def __init__(self, config: HydraConfig, *args, **kwargs):
        super().__init__("", *args, **kwargs)
        self.config = config
        self._group_nodes: dict[str, TreeNode] = {}
        self.border_title = "⚙️  Config Groups"
        self.show_root = False
        self.show_guides = True

    def on_mount(self) -> None:
        """Build the tree when mounted."""
        self.root.expand()
        self.build_tree()

    def build_tree(self) -> None:
        """Build the tree structure from config data."""

        # Custom sort: _ prefixed items go last
        def sort_key(item):
            name = item[0]
            # Items starting with _ sort last
            if name.startswith("_"):
                return (1, name)  # High priority (sorts last)
            else:
                return (0, name)  # Normal priority

        # Sort config groups: those with values first, "not set" last
        groups_with_values = []
        groups_without_values = []

        for group_name, group in sorted(self.config.groups.items(), key=sort_key):
            if group.selected:
                groups_with_values.append((group_name, group))
            else:
                groups_without_values.append((group_name, group))

        # Add config groups with values first (expandable with options as children)
        for group_name, group in groups_with_values:
            display_value = group.get_display_value()

            # Format the label with visual indicators
            # Only show lightning if multirun AND multiple values
            if group.multirun and len(group.selected) > 1:
                label = f"⚡ [bold cyan]{group_name}[/bold cyan] [dim]=[/dim] [magenta]{display_value}[/magenta]"
            else:
                label = f"[bold cyan]{group_name}[/bold cyan] [dim]=[/dim] [green]{display_value}[/green]"

            # Additional style if modified
            if group.is_modified():
                label = f"[yellow]✎[/yellow] {label}"

            # Add as parent node with options as children
            parent_node = self.root.add(label, data=f"group:{group_name}", expand=False)
            self._group_nodes[group_name] = parent_node

            # Sort options: _ prefixed items go last
            sorted_options = sorted(group.options, key=lambda opt: (1, opt) if opt.startswith("_") else (0, opt))

            # Add options as children
            for option in sorted_options:
                if group.multirun:
                    # Multirun: checkbox
                    if option in group.selected:
                        icon = "☑"
                        option_label = f"[green]{icon}[/green] [bold]{option}[/bold]"
                    else:
                        icon = "☐"
                        option_label = f"[dim]{icon}[/dim] {option}"
                else:
                    # Single: radio button
                    if option in group.selected:
                        icon = "●"
                        option_label = f"[green]{icon}[/green] [bold]{option}[/bold]"
                    else:
                        icon = "○"
                        option_label = f"[dim]{icon}[/dim] {option}"

                parent_node.add_leaf(option_label, data=f"option:{group_name}:{option}")

        # Add groups without values (expandable)
        for group_name, group in groups_without_values:
            # If group had an original value but now empty, show as delete
            if group.original_selected:
                label = f"[red]🗑[/red]  [bold orange]{group_name}[/bold orange] [dim]=[/dim] [red]delete[/red]"
            else:
                label = f"[dim]{group_name} = not set[/dim]"

            parent_node = self.root.add(label, data=f"group:{group_name}", expand=False)
            self._group_nodes[group_name] = parent_node

            # Sort options: _ prefixed items go last
            sorted_options = sorted(group.options, key=lambda opt: (1, opt) if opt.startswith("_") else (0, opt))

            # Add options as children
            for option in sorted_options:
                if group.original_selected:
                    icon = "○"
                    option_label = f"[dim]{icon}[/dim] {option}"
                else:
                    icon = "○"
                    option_label = f"[dim]{icon} {option}[/dim]"
                parent_node.add_leaf(option_label, data=f"option:{group_name}:{option}")

    def refresh_tree(self) -> None:
        """Refresh the tree display after changes."""
        # Instead of rebuilding, update labels of existing nodes
        for group_name, parent_node in self._group_nodes.items():
            group = self.config.groups.get(group_name)
            if not group:
                continue

            display_value = group.get_display_value()

            # Format the parent label with visual indicators
            if group.selected:
                # Only show lightning if multirun AND multiple values
                if group.multirun and len(group.selected) > 1:
                    label = f"⚡ [bold cyan]{group_name}[/bold cyan] [dim]=[/dim] [magenta]{display_value}[/magenta]"
                else:
                    label = f"[bold cyan]{group_name}[/bold cyan] [dim]=[/dim] [green]{display_value}[/green]"

                # Additional style if modified
                if group.is_modified():
                    label = f"[yellow]✎[/yellow] {label}"
            else:
                # If group had an original value but now empty, show as delete
                if group.original_selected:
                    label = f"[red]🗑[/red]  [bold orange]{group_name}[/bold orange] [dim]=[/dim] [red]delete[/red]"
                else:
                    label = f"[dim]{group_name} = not set[/dim]"

            # Update the parent node's label
            parent_node.set_label(label)

            # Sort options: _ prefixed items go last (same as build_tree)
            sorted_options = sorted(group.options, key=lambda opt: (1, opt) if opt.startswith("_") else (0, opt))

            # Update all child option nodes
            for i, child_node in enumerate(parent_node.children):
                if i < len(sorted_options):
                    option = sorted_options[i]

                    # Determine icon based on selection mode and state
                    if group.selected:
                        if group.multirun:
                            if option in group.selected:
                                icon = "☑"
                                option_label = f"[green]{icon}[/green] [bold]{option}[/bold]"
                            else:
                                icon = "☐"
                                option_label = f"[dim]{icon}[/dim] {option}"
                        else:
                            if option in group.selected:
                                icon = "●"
                                option_label = f"[green]{icon}[/green] [bold]{option}[/bold]"
                            else:
                                icon = "○"
                                option_label = f"[dim]{icon}[/dim] {option}"
                    else:
                        # Group not set
                        icon = "○"
                        if group.original_selected:
                            # Had value before - show normally (deletion context)
                            option_label = f"[dim]{icon}[/dim] {option}"
                        else:
                            # Never had value - dim
                            option_label = f"[dim]{icon} {option}[/dim]"

                    child_node.set_label(option_label)

    def get_selected_item(self) -> tuple[str, str, str | None] | None:
        """Get the currently selected item.

        Returns:
            Tuple of (type, group_name, option_name) where:
            - type is 'group' or 'option'
            - group_name is the config group
            - option_name is the specific option (only for 'option' type)
        """
        node = self.cursor_node
        if not node or not node.data:
            return None

        if node.data.startswith("group:"):
            group_name = node.data.split(":", 1)[1]
            return ("group", group_name, None)
        elif node.data.startswith("option:"):
            parts = node.data.split(":", 2)
            if len(parts) == 3:
                return ("option", parts[1], parts[2])

        return None

    def on_tree_node_selected(self, event) -> None:
        """Handle tree node selection (mouse click or Enter key)."""
        selected = self.get_selected_item()

        if not selected:
            return

        item_type, group_name, option_name = selected

        # Click/Enter on option: treat as single select
        if item_type == "option":
            event.stop()
            self.post_message(self.OptionSelected(group_name, option_name, is_multirun=False))
        # Click/Enter on group: let default expand/collapse happen

    def on_key(self, event: events.Key) -> None:
        """Handle key presses for Space (multirun toggle)."""
        selected = self.get_selected_item()

        if not selected:
            return

        item_type, group_name, option_name = selected

        # Handle Space: multirun toggle
        if event.key == "space" and item_type == "option":
            event.prevent_default()
            event.stop()
            self.post_message(self.OptionSelected(group_name, option_name, is_multirun=True))


class ConfigValueTree(Tree[str]):
    """Tree widget for displaying config values in hierarchical structure."""

    def __init__(self, config: HydraConfig, *args, **kwargs):
        super().__init__("", *args, **kwargs)
        self.config = config
        self._value_nodes: dict[str, TreeNode] = {}
        self.border_title = "📝 Config Values"
        self.show_root = False
        self.show_guides = True

    def on_mount(self) -> None:
        """Build the tree when mounted."""
        self.root.expand()
        self.build_tree()

    def build_tree(self) -> None:
        """Build hierarchical tree structure from config values."""
        # Build a tree structure from paths
        tree_structure = {}

        for path, config_value in self.config.values.items():
            parts = path.split(".")
            current = tree_structure

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {}

                # Store the value at the leaf
                if i == len(parts) - 1:
                    current[part]["__value__"] = config_value
                else:
                    if "__children__" not in current[part]:
                        current[part]["__children__"] = {}
                    current = current[part]["__children__"]

        # Recursively build tree nodes
        self._build_nodes(self.root, tree_structure, "")

    def _build_nodes(self, parent: TreeNode, structure: dict, prefix: str) -> None:
        """Recursively build tree nodes from structure."""

        # Custom sort: _ prefixed items go last
        def sort_key(key):
            if key.startswith("_"):
                return (1, key)  # High priority (sorts last)
            else:
                return (0, key)  # Normal priority

        for key in sorted(structure.keys(), key=sort_key):
            value_dict = structure[key]
            full_path = f"{prefix}.{key}" if prefix else key

            # Check if this is a leaf (has __value__)
            if "__value__" in value_dict:
                config_value = value_dict["__value__"]
                display_value = config_value.get_display_value()
                label = f"[cyan]{key}[/cyan] [dim]=[/dim] {display_value}"

                # Style based on modification status
                if config_value.is_modified():
                    label = (
                        f"[yellow]✎[/yellow] [cyan]{key}[/cyan] [dim]=[/dim] [bold green]{display_value}[/bold green]"
                    )

                node = parent.add_leaf(label, data=f"value:{full_path}")
                self._value_nodes[full_path] = node

            # Check if this has children
            elif "__children__" in value_dict:
                node = parent.add(key, expand=False)
                self._build_nodes(node, value_dict["__children__"], full_path)

    def refresh_tree(self) -> None:
        """Refresh the tree display after changes."""
        # Update labels of existing value nodes
        for path, node in self._value_nodes.items():
            config_value = self.config.values.get(path)
            if not config_value:
                continue

            display_value = config_value.get_display_value()
            # Extract just the key (last part of path)
            key = path.split(".")[-1]
            label = f"[cyan]{key}[/cyan] [dim]=[/dim] {display_value}"

            # Style based on modification status
            if config_value.is_modified():
                label = f"[yellow]✎[/yellow] [cyan]{key}[/cyan] [dim]=[/dim] [bold green]{display_value}[/bold green]"

            # Update the node's label
            node.set_label(label)

        # Force the tree widget to refresh its display
        self.refresh(repaint=True)

    def get_selected_item(self) -> tuple[str, str] | None:
        """Get the currently selected item.

        Returns:
            Tuple of ('value', path)
        """
        node = self.cursor_node
        if node and node.data and node.data.startswith("value:"):
            return ("value", node.data.split(":", 1)[1])
        return None
