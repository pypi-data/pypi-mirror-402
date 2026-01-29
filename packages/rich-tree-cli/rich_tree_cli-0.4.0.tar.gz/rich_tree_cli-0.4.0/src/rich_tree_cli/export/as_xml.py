"""Xml export for RichTreeCLI."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    from rich_tree_cli.output_manager import DataResult


def build_xml(data: DataResult) -> str:
    """Build an XML representation of the directory structure."""
    from xml.etree.ElementTree import Element, ElementTree, SubElement, indent  # noqa: PLC0415

    root_path: Path = data.root

    def add_element(path: Path, parent: Element) -> None:
        # Ensure we have an absolute path for file operations
        abs_path: Path = path if path.is_absolute() else root_path / path
        tag: Literal["directory", "file"] = "directory" if abs_path.is_dir() else "file"
        element: Element = SubElement(parent, tag, name=abs_path.name)
        if abs_path.is_dir():
            for item in data.cached_paths.get_items(abs_path):
                add_element(item.path, element)
        else:
            element.set("size", str(abs_path.stat().st_size))
            try:
                lines: int = len(abs_path.read_text(encoding="utf-8").splitlines())
            except UnicodeDecodeError:
                lines = 0
            element.set("lines", str(lines))

    root_element: Element = Element(
        "structure",
        {
            "total_dirs": str(data.dir_count),
            "total_files": str(data.file_count),
            "root_path": str(data.root.resolve()),
        },
    )
    add_element(data.root, root_element)

    tree: ElementTree = ElementTree(root_element)
    indent(tree, space="  ")
    xml_io = io.StringIO()
    tree.write(xml_io, encoding="unicode")
    return xml_io.getvalue()
