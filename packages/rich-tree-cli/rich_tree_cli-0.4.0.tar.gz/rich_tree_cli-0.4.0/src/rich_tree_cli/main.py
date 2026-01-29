"""Rich Tree CLI: A command-line interface for displaying directory trees in a rich format."""

from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING, cast

from rich.tree import Tree

from ._args import CLIArgs, get_args

if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console

    from ._models import DataResult, PathsContainer
    from .export.icons import IconManager, IconMode
    from .ignore_handler import IgnoreHandler
    from .output_manager import OutputManager


class RichTreeCLI:
    """RichTreeCLI class to build and display a directory tree with various options."""

    def __init__(self, args: CLIArgs) -> None:
        """Initialize the RichTree from CLI arguments."""
        self.args: CLIArgs = args
        self.root: Path = args.directory
        self.file_count = 0
        self.dir_count = 0

        self._ignore_handler: IgnoreHandler | None = None
        self._output_manager: OutputManager | None = None
        self._paths: PathsContainer | None = None
        self._icon: IconManager | None = None
        self._console: Console | None = None

        self.tree = Tree(f"{self.icon.folder_default}  {self.root.name}")

    def _is_ignored(self, path: Path) -> bool:
        """Fast O(1) check if path is ignored using pre-computed set."""
        return str(path) not in self.paths.cached_paths

    def add_to_tree(self, path: Path, tree_node: Tree, current_depth: int = 0) -> None:
        """Recursively add items to the tree structure."""
        if self.args.max_depth and current_depth >= self.args.max_depth:
            return

        for item in self.paths.get_items(path):
            is_dir: bool = item.is_dir()
            icon: str = item.to_string(
                self.icon,
                self.args.metadata,
                self.args.datefmt,
                self.args.duration,
            )
            if is_dir:
                branch: Tree = tree_node.add(icon, highlight=True, style="bold green")
                self.dir_count += 1
                self.add_to_tree(item.path, branch, current_depth + 1)
            else:
                tree_node.add(icon, highlight=False, style="dim white")
                self.file_count += 1

    @property
    def totals(self) -> str:
        """Return a string with the total counts of directories and files."""
        return f"{self.dir_count} directories, {self.file_count} files"

    @property
    def console(self) -> Console:
        """Lazily initialize and return the console."""
        if self._console is None:
            if not self.args.no_console:
                from ._get_console import get_console

                self._console = get_console(disable_color=self.args.no_color)
            else:
                from ._models import NullConsole

                self._console = cast("Console", NullConsole())
        return self._console

    @property
    def ignore_handler(self) -> IgnoreHandler:
        """Lazily initialize and return the IgnoreHandler."""
        from .ignore_handler import IgnoreHandler

        if self._ignore_handler is None:
            exclude: list[str] | None = self.args.exclude if self.args.exclude else None
            self._ignore_handler = IgnoreHandler(gitignore_file=self.args.gitignore_path, patterns=exclude)
        return self._ignore_handler

    @property
    def output_manager(self) -> OutputManager | None:
        """Lazily initialize and return the OutputManager if output is specified."""
        if self.args.output and self._output_manager is None:
            from .output_manager import OutputManager

            self._output_manager = OutputManager(disable_color=self.args.no_color)
        return self._output_manager

    @property
    def paths(self) -> PathsContainer:
        """Lazily initialize and return the PathsContainer."""
        from ._models import PathsContainer

        if self._paths is None:
            self._paths = PathsContainer.create(
                root_path=self.root,
                spec=self.ignore_handler.spec,
                sort_order=self.args.sort_order,
            )
        return self._paths

    @property
    def icon(self) -> IconManager:
        """Lazily initialize and return the IconManager."""
        from .export.icons import IconManager, get_mode

        if self._icon is None:
            mode: IconMode = get_mode(self.args.icons)
            self._icon = IconManager(mode=mode)
        return self._icon

    def run(self) -> DataResult:
        """Build the tree and return results for the :class:`OutputManager`."""
        from ._models import DataResult

        self.add_to_tree(path=self.root, tree_node=self.tree)
        return DataResult(
            tree=self.tree,
            root=self.root,
            sort_order=self.args.sort_order,
            dir_count=self.dir_count,
            file_count=self.file_count,
            totals=self.totals,
            max_depth=self.args.max_depth,
            cached_paths=self.paths,
        )


def main(arguments: list[str] | None = None) -> int:
    """Main function to run the RichTreeCLI."""
    if arguments is None:
        arguments = sys.argv[1:]

    args: CLIArgs = get_args(arguments)
    if not args.directory.is_dir() or not args.directory.exists():
        print(f"Error: {args.directory} is not a valid directory.", file=sys.stderr)
        return 1
    try:
        cli = RichTreeCLI(args)
        data: DataResult = cli.run()
        cli.console.print(data.tree)
        cli.console.print(f"\n{data.totals}\n", style="bold green")
        if args.output and cli.output_manager is not None:
            cli.output_manager.output(data, args.output_format, args.output)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# ruff: noqa: PLC0415
