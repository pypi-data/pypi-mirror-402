from dataclasses import asdict, dataclass
from io import StringIO

from rich.console import Console

POSSIBLE_OPTIONS: frozenset[str] = frozenset(
    {
        "file",
        "highlight",
        "soft_wrap",
        "width",
        "emoji",
        "emoji_variant",
        "markup",
        "record",
        "force_terminal",
        "style",
        "no_color",
    }
)


@dataclass(slots=True)
class ConsoleConfig:
    """Configuration for the console."""

    file: StringIO | None = None
    highlight: bool = True
    soft_wrap: bool = True
    width: int | None = None
    emoji: bool = True
    emoji_variant: str = "emoji"
    markup: bool = True
    record: bool = False
    force_terminal: bool | None = None
    style: str | None = None
    no_color: bool | None = None
    stderr: bool = False

    def update(self, **kwargs) -> None:
        """Update the console configuration with additional keyword arguments."""
        for key, value in kwargs.items():
            if key in POSSIBLE_OPTIONS:
                setattr(self, key, value)


def get_console(disable_color: bool, **kwargs) -> Console:
    """Create the output and capture consoles with the specified configurations."""
    base_config = ConsoleConfig()
    if file := kwargs.pop("file", None):
        base_config.file = file
    if disable_color:
        base_config.highlight = False
        base_config.markup = False
        base_config.force_terminal = False
        base_config.no_color = True

    if kwargs:  # allows an override anything that comes before this
        base_config.update(**kwargs)

    return Console(**asdict(base_config))
