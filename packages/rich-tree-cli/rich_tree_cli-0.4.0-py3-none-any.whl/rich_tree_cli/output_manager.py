"""Python module to manage output for RichTreeCLI, including file exports and console rendering."""

from __future__ import annotations

from io import StringIO
import json
from typing import TYPE_CHECKING, cast

from ._get_console import get_console
from .constants import OutputFormat

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from rich.console import Console

    from ._models import DataResult


def _to_text(data: DataResult, **kwargs) -> str:
    capture: Console = kwargs.get("capture", "")
    if not capture:
        return ""
    return capture.export_text()


def _to_toml(data: DataResult, **kwargs) -> str:
    from .export.as_json import build_json
    from .export.as_toml import build_toml

    json_output: str = json.dumps(build_json(data, data.root), indent=2)
    return build_toml(json_data=json.loads(json_output))


def _to_html(data: DataResult, **kwargs) -> str:
    from .export.as_html import build_html

    return build_html(data)


def _to_markdown(data: DataResult, **kwargs) -> str:
    tree_str: str = kwargs.get("tree_str", "")
    return f"# Directory Structure\n\n```plain\n{tree_str}\n```\n\n{data.totals}\n"


def _to_json(data: DataResult, **kwargs) -> str:
    from .export.as_json import build_json

    return json.dumps(build_json(data, data.root), indent=2)


def _to_svg(data: DataResult, **kwargs) -> str:
    capture: Console = kwargs.get("capture", "")
    if not capture:
        return ""
    return capture.export_svg()


def _to_xml(data: DataResult, **kwargs) -> str:
    from .export.as_xml import build_xml

    return build_xml(data)


FUNC_LIST: list[Callable[..., str]] = [
    _to_text,
    _to_markdown,
    _to_html,
    _to_json,
    _to_svg,
    _to_toml,
    _to_xml,
]


class OutputManager:
    """Handle writing output files for export."""

    def __init__(self, disable_color: bool = False) -> None:
        """Initialize the OutputManager with an optional color setting."""
        self.disable_color: bool = disable_color

    def generate_output(self, func: Callable[..., str], data: DataResult) -> str:
        """Generate the output in the specified format."""
        capture: Console = get_console(disable_color=True, record=True, file=StringIO())
        output_buffer: StringIO = cast("StringIO", capture.file)
        capture.print(data.tree)
        result: str = output_buffer.getvalue()
        result = func(data, tree_str=result, totals=data.totals, capture=capture)
        output_buffer.close()
        return result or capture.export_text()

    def output(self, data: DataResult, output_formats: list[str], output_path: Path) -> None:
        """Write output files in the specified formats."""
        for fmt in output_formats:
            fmt_id: OutputFormat = OutputFormat.key_to_fmt(fmt)
            func: Callable[..., str] = FUNC_LIST[fmt_id]
            out_str: str = self.generate_output(func, data)
            ext: str = f".{OutputFormat.to_ext(fmt)}"
            out_file: Path = output_path.with_name(f"{output_path.stem}{ext}")
            out_file.write_text(out_str, encoding="utf-8")


# ruff: noqa: PLC0415, ARG001
