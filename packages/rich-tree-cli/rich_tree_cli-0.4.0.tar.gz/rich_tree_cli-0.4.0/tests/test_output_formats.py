import json
from pathlib import Path
import tomllib
from typing import TYPE_CHECKING

from defusedxml.ElementTree import fromstring as fromstring_defused

from rich_tree_cli._args import CLIArgs
from rich_tree_cli.main import RichTreeCLI
from rich_tree_cli.output_manager import OutputManager

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

OUTPUT_FORMATS: list[str] = ["text", "markdown", "html", "json", "svg", "toml", "xml"]


def test_output_formats(tmp_path: Path) -> None:
    output_dir: Path = Path(__file__).parent / "output"
    output_base: Path = output_dir / "test_output"
    try:
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "file.txt").write_text("content")
        (tmp_path / "root.txt").write_text("root")

        args = CLIArgs(
            directory=tmp_path,
            output=output_base,
            output_format=OUTPUT_FORMATS,
            no_color=True,
            no_console=True,
            metadata=["size", "lines", "created", "modified"],
        )
        cli = RichTreeCLI(args)
        manager = OutputManager(disable_color=True)
        result = cli.run()
        manager.output(result, OUTPUT_FORMATS, output_base)

        ext_map = {
            "text": ".txt",
            "markdown": ".md",
            "html": ".html",
            "json": ".json",
            "svg": ".svg",
            "toml": ".toml",
            "xml": ".xml",
        }
        for _, ext in ext_map.items():
            output_file = output_base.with_suffix(ext)
            assert output_file.exists()
            assert output_file.stat().st_size > 0

        json_data = json.loads(output_base.with_suffix(".json").read_text(encoding="utf-8"))
        assert "tree" in json_data
        xml_content = output_base.with_suffix(".xml").read_text(encoding="utf-8")
        xml_data: Element[str] = fromstring_defused(xml_content)
        assert xml_data.tag == "structure"

        toml_data = tomllib.loads(output_base.with_suffix(".toml").read_text(encoding="utf-8"))
        assert "metadata" in toml_data
        assert "tree" in toml_data

    finally:
        for subdir in output_dir.iterdir():
            if subdir.is_dir():
                for file in subdir.iterdir():
                    file.unlink(missing_ok=True)
                subdir.rmdir()

        for fmt in ["txt", "md", "html", "svg", "json", "toml", "xml"]:
            output_file = output_base.with_suffix(f".{fmt}")
            output_file.unlink(missing_ok=True)
