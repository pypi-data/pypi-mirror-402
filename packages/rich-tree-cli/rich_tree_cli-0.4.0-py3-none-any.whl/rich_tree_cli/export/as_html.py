"""# Python module to export directory structures as HTML for RichTreeCLI."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from rich.tree import Tree

from rich_tree_cli.file_info import PathObj

from ._common import VSC_IN, URIScheme, jinja_template as jt
from .icons import IconManager, IconMode

if TYPE_CHECKING:
    from pathlib import Path

    from rich_tree_cli.output_manager import DataResult


CLASS_FOLDER = "class='folder'"
CLASS_FILE = "class='file'"
CLASS_HIDDEN = "class='hidden'"
DIGEST_SIZE = 10


def build_html(data: DataResult) -> str:
    """Build an HTML representation of the directory structure for RichTreeCLI."""
    html_template = HTMLHandler(data)
    return html_template.render()


class HTMLHandler:
    """Class to handle HTML export of the directory structure for RichTreeCLI."""

    def __init__(self, data: DataResult, uri_mode: URIScheme = VSC_IN) -> None:
        """Initialize the HTMLHandler with a RichTreeCLI instance."""
        from io import StringIO

        from rich.console import Console

        self.data: DataResult = data
        self.icon = IconManager(mode=IconMode.SVG_ICONS)
        self.root: Path = data.root.resolve()
        self.template_map: SimpleNamespace = SimpleNamespace()
        self.tree = Tree(self.link(path=self.root, uri=uri_mode, cls_name=CLASS_FOLDER), highlight=True)
        self.capture: Console = Console(record=True, markup=False, file=StringIO(), emoji=True, soft_wrap=False)
        self.add_to_html_tree(path=data.root, tree_node=self.tree, current_depth=data.max_depth)
        self.capture.print(self.tree)

    def link(self, path: Path, uri: URIScheme, cls_name: str) -> str:
        """Create a link and return a Jinja2 hash reference to avoid Rich formatting issues.

        Generates an HTML link with icon and styling, stores it in the template map using
        a hash as the attribute name, and returns {{ hash.{href_hash} }} for dot notation
        access in Jinja2 templates. This keeps Rich trees clean while preserving full links.

        Args:
            path (Path): The file path to link to.
            uri (URIScheme): The URI scheme to use, e.g., FILE or VSC_IN.
            cls_name (str): CSS class to apply to the link.

        Returns:
            str: Jinja2 template variable "{{ hash.{href_hash} }}" for dot notation access.

        Raises:
            ValueError: If a hash collision is detected.
        """

        def _hash_key(hashable: str, digest_size: int = DIGEST_SIZE) -> str:
            return f"h{abs(hash(hashable)) & ((1 << (digest_size * 8)) - 1):x}"

        from urllib.parse import quote

        label: str = f"{self.icon.get(path)} {path.name}"
        a_href = '<a href="{url}" {cls}>{label}</a>'
        link: str = f"{uri}{quote(str(path.resolve()), safe='/')}"
        a_href: str = a_href.format(url=link, cls=cls_name, label=label)
        href_hash: str = _hash_key(a_href)
        if hasattr(self.template_map, href_hash):
            raise ValueError(f"WEE WOO! Hash collision detected: {href_hash} for {path}. WEE WOO!")
        setattr(self.template_map, href_hash, a_href)
        return jt(f"hash.{href_hash}")

    def add_to_html_tree(
        self,
        path: Path,
        tree_node: Tree,
        current_depth: int = 0,
    ) -> Tree:
        """Recursively add items to the tree structure.

        Args:
            path (Path): The current directory path.
            tree_node (Tree): The current tree node to add items to.
            current_depth (int): The current depth in the directory structure.

        Returns:
            Tree: The updated tree node with items added.
        """
        if self.data.max_depth and current_depth >= self.data.max_depth:
            return tree_node

        if isinstance(path, PathObj):
            path = path.path

        for item in self.data.cached_paths.get_items(path):
            if item.is_dir():
                branch: Tree = tree_node.add(
                    label=self.link(path=item, uri=VSC_IN, cls_name=CLASS_FOLDER),
                    highlight=True,
                )
                self.add_to_html_tree(path=item, tree_node=branch, current_depth=current_depth + 1)
            else:
                file: str = self.link(path=item, uri=VSC_IN, cls_name=CLASS_FILE)
                hidden: str = self.link(path=item, uri=VSC_IN, cls_name=CLASS_HIDDEN)
                cls_func: str = hidden if item.name.startswith(".") else file
                tree_node.add(label=cls_func, highlight=False)
        return tree_node

    def render(self) -> str:
        """Build HTML output from the captured console output.

        Args:
            capture (Console): The console object that has captured the output.

        Returns:
            str: The HTML formatted string.
        """
        from jinja2 import Template

        from .html.html_template import HTML_TEMPLATE, STYLES_CSS

        tree: str = self.capture.export_text()
        ##########################
        ### FOR DEBUGGING ONLY ###
        # with open("hash_test.txt", "w", encoding="utf-8") as f:
        #     f.write(tree)
        ##########################
        html = Template(HTML_TEMPLATE.render(defined_css=STYLES_CSS, tree_content=tree, totals=self.data.totals))
        return html.render(hash=self.template_map)


# ruff: noqa: PLC0415
