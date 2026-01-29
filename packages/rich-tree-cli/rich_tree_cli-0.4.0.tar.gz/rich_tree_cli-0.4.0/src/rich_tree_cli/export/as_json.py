"""Python module to build a JSON representation of a directory structure for RichTreeCLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from rich_tree_cli.output_manager import DataResult


def build_json(data: DataResult, path: Path) -> dict:
    """Build a dictionary representation of the directory structure."""
    if path == data.root:
        tree_data: dict[str, str] = build_tree_dict(data, path)
        return {
            "metadata": {
                "total_dirs": data.dir_count,
                "total_files": data.file_count,
                "root_path": str(data.root),
            },
            "tree": tree_data,
        }
    return build_tree_dict(data, path)


def build_tree_dict(data: DataResult, path: Path) -> dict:
    """Build a more compact tree representation."""
    result: dict[str, Any] = {}
    for item in data.cached_paths.get_items(path):
        if item.is_dir():
            result[item.name + "/"] = build_tree_dict(data, item.path)
        else:
            result[item.name] = {"size": item.size, "lines": item.length}
    return result
