"""RichTreeCLI constants and data classes."""

from __future__ import annotations

from enum import Enum, IntEnum
from importlib.metadata import version
from pathlib import Path
from typing import Any, Final, Literal, Self

CONFIG_PATH: Final[Path] = Path.home() / ".config" / "rich_tree_cli" / "config.toml"

type SortChoice = Literal["files", "dirs", "size", "modified", "created"]
SORT_CHOICES: Final[list[str]] = ["files", "dirs", "size", "modified", "created"]

type IconChoice = Literal["plain", "emoji", "glyphs"]
ICON_CHOICES: Final[list[str]] = ["plain", "emoji", "glyphs"]

type MetaDataChoice = Literal["none", "size", "lines", "created", "modified", "all"]
METADATA_CHOICES: Final[list[str]] = ["none", "size", "lines", "created", "modified", "all"]
ALL_METADATA: Final[list[str]] = ["size", "lines", "created", "modified"]

DEFAULT_FMT: Final[list[str]] = ["text"]

FIELD_NAMES: list[str] = [
    "max_depth",
    "datefmt",
    "icons",
    "sort_order",
    "debug",
    "no_color",
    "no_console",
    "duration",
    "gitignore_path",
    "metadata",
    "output_format",
]

DEFAULT_GITIGNORE_PATH: Path = Path(".gitignore")
FIELD_NAME_SET: set[str] = {*FIELD_NAMES, "exclude"}

type TomlData = dict[str, dict[str, Any]]

KILOBYTES: Literal[1024] = 1024
MEGABYTES: Literal[1048576] = KILOBYTES * 1024
IS_BINARY = -1

YEAR: Literal[365] = 365
MONTH: Literal[30] = 30
WEEK: Literal[7] = 7
DAY: Literal[1] = 1
DAY_TO_HOURS: Literal[24] = 24
DAY_TO_MIN: Literal[1440] = DAY_TO_HOURS * 60
SECONDS: Literal[86400] = 60 * 60 * DAY_TO_HOURS


class OS(Enum):
    """Enum for operating system platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    UNKNOWN = "unknown"


EXT_MAP: dict[OutputFormat, str] = {}


class OutputFormat(IntEnum):
    """Enum for output formats."""

    TEXT = 0
    MARKDOWN = 1
    HTML = 2
    JSON = 3
    SVG = 4
    TOML = 5
    XML = 6

    @classmethod
    def to_ext(cls, name: str, default: str = ".txt", ext_map: dict[OutputFormat, str] = EXT_MAP) -> str:
        """Get the file extension for the output format."""
        return ext_map.get(cls.key_to_fmt(name), default)

    @classmethod
    def key_to_fmt(cls, key: str) -> Self:
        """Get the value of the enum based on the key."""
        try:
            return cls[key.upper()]
        except KeyError:
            raise ValueError(f"Invalid output format key: {key}") from None

    @classmethod
    def choices(cls) -> list[str]:
        """Return a list of available output format choices."""
        return [format.name.lower() for format in cls]

    @classmethod
    def default(cls) -> list[str]:
        """Return the default output format."""
        default: Literal[OutputFormat.TEXT] = OutputFormat.TEXT

        return [default.name.lower()]


for format_enum, extension in [
    (OutputFormat.TEXT, "txt"),
    (OutputFormat.MARKDOWN, "md"),
    (OutputFormat.HTML, "html"),
    (OutputFormat.JSON, "json"),
    (OutputFormat.SVG, "svg"),
    (OutputFormat.TOML, "toml"),
    (OutputFormat.XML, "xml"),
]:
    EXT_MAP[format_enum] = extension


__version__: str = version("rich-tree-cli")
