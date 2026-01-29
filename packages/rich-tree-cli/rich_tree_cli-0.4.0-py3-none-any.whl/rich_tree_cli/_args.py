from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any

from ._models import EMPTY_LIST
from .constants import (
    ALL_METADATA,
    CONFIG_PATH,
    DEFAULT_FMT,
    DEFAULT_GITIGNORE_PATH,
    FIELD_NAME_SET,
    FIELD_NAMES,
    ICON_CHOICES,
    METADATA_CHOICES,
    SORT_CHOICES,
    IconChoice,
    OutputFormat,
    SortChoice,
    TomlData,
    __version__,
)


@dataclass(slots=True)
class Config:
    """Configuration settings loaded from config file."""

    max_depth: int | None = None
    datefmt: str | None = None
    icons: IconChoice | None = None
    sort_order: SortChoice | None = None

    debug: bool | None = None
    no_color: bool | None = None
    no_console: bool | None = None
    duration: bool | None = None

    gitignore_path: Path | None = None
    metadata: list[str] | None = None
    output_format: list[str] | None = None
    exclude: list[str] | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load configuration from TOML file.

        Args:
            path: Path to config file. Defaults to ~/.config/rich_tree_cli/config.toml

        Example config file:
            [defaults]
            max_depth = 3
            datefmt = "%Y-%m-%d %H:%M"
            icons = "emoji"
            sort = "files"

            debug = false
            no_color = false
            no_console = false
            duration = false

            gitignore_path = "~/.gitignore"
            metadata = ["size", "modified"]
            format = ["text"]
            exclude = ["node_modules", "__pycache__", ".git", "*.pyc"]
        """
        config_path: Path = path or CONFIG_PATH
        if not config_path.exists():
            return cls()
        try:
            with config_path.open("rb") as f:
                data: TomlData = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return cls()

        return cls(**{k: v for k, v in data.get("defaults", {}).items() if k in FIELD_NAME_SET})


@dataclass(slots=True)
class CLIArgs:
    """Typed container for all CLI arguments."""

    directory: Path = field(default_factory=Path.cwd)
    output: Path | None = None
    version: str = __version__

    max_depth: int = field(default=0)
    datefmt: str = "%Y-%m-%d %H:%M"
    icons: IconChoice = "emoji"
    sort_order: SortChoice = "files"

    debug: bool = False
    no_color: bool = False
    no_console: bool = False
    duration: bool = False

    gitignore_path: Path | None = None
    metadata: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    output_format: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.max_depth = abs(self.max_depth)

    def update(self, config: Config, ns: Namespace) -> CLIArgs:
        """Update CLIArgs instance with values from config where not set in Namespace.

        Args:
            config: Config instance with default settings.
            ns: Namespace instance with parsed CLI arguments.

        Returns:
            Updated CLIArgs instance.
        """
        if hasattr(ns, "directory") and ns.directory is not None:
            self.directory = Path(ns.directory).expanduser().resolve()
        for field_name in FIELD_NAMES:
            config_value: Any | None = getattr(config, field_name, None)
            ns_value: Any | None = getattr(ns, field_name, None)
            ns_has: bool = ns_value is not None
            config_has: bool = config_value is not None
            if (ns_has and config_has) or (ns_has and not config_has):
                setattr(self, field_name, ns_value)  # CLI overrides config
            elif config_has and not ns_has:
                setattr(self, field_name, config_value)  # config used if CLI not set
        if not self.output_format:
            self.output_format = DEFAULT_FMT
        if "all" in self.metadata:
            self.metadata = ALL_METADATA
        elif "none" in self.metadata:
            self.metadata = EMPTY_LIST
        if config.exclude is not None:
            self.exclude = list(set(ns.exclude + config.exclude))
        return self


def get_args(args: list[str], config: Config | None = None) -> CLIArgs:
    """Parse command line arguments and merge with config file defaults.

    Priority order: CLI args > config file > built-in defaults

    Args:
        args (list[str]): List of command line arguments.
        config (Config): Configuration object.

    Returns:
        CLIArgs: Typed container with all parsed arguments.
    """
    if config is None:
        config = Config.load()

    parser = ArgumentParser(description="Display a directory tree in a rich format.", prog="rtree")
    parser.add_argument("directory", nargs="?", default=None, help="Directory to display")

    parser.add_argument(
        "--depth",
        "-d",
        type=int,
        default=None,
        dest="max_depth",
        help="Maximum depth of the tree (0 for no limit)",
    )
    parser.add_argument(
        "--datefmt",
        type=str,
        default=None,
        help='Date format for metadata (default: "%(default)s")',
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path (extension determined by format)",
    )

    parser.add_argument(
        "--duration",
        action="store_const",
        const=True,
        default=None,
        dest="duration",
        help="Display duration of modified/created times",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=OutputFormat.choices(),
        nargs="+",
        default=None,
        dest="output_format",
        help=f"Output format(s): {', '.join(OutputFormat.choices())} (default: text)",
    )

    parser.add_argument(
        "--metadata",
        "-m",
        choices=METADATA_CHOICES,
        nargs="*",
        default=None,
        help="Metadata to display: size, lines, created, modified, all, none (default: none)",
    )

    parser.add_argument(
        "--exclude",
        "-e",
        default=EMPTY_LIST,
        nargs="+",
        help="Exclude files/directories matching patterns",
    )

    parser.add_argument(
        "--gitignore",
        "-g",
        nargs="?",
        const=DEFAULT_GITIGNORE_PATH,
        default=None,
        dest="gitignore_path",
        help="Use .gitignore file (optionally specify path)",
    )

    parser.add_argument(
        "--sort",
        "-s",
        choices=SORT_CHOICES,
        default=None,
        dest="sort_order",
        help="Sort order: files first or dirs first (default: files)",
    )

    parser.add_argument(
        "--icons",
        "-i",
        type=str,
        default=None,
        choices=ICON_CHOICES,
        help="Icon style: plain, emoji, glyphs (default: emoji)",
    )

    parser.add_argument(
        "--no-color",
        action="store_const",
        const=True,
        default=None,
        dest="no_color",
        help="Disable colored output",
    )

    parser.add_argument(
        "--no-console",
        action="store_const",
        const=True,
        default=None,
        dest="no_console",
        help="Suppress terminal output (export only)",
    )

    parser.add_argument(
        "--debug",
        action="store_const",
        const=True,
        default=None,
        dest="debug",
        help="Enable debug mode",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"rtree v{__version__}",
        help="Show version",
    )

    parsed_args: Namespace = parser.parse_args(args)
    return CLIArgs().update(config, parsed_args)
