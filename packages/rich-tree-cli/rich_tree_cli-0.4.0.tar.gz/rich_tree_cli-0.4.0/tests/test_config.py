"""Tests for configuration file loading."""

from argparse import Namespace
from pathlib import Path

from rich_tree_cli._args import CLIArgs, Config, get_args
from rich_tree_cli.constants import ALL_METADATA


def test_config_defaults():
    """Test that Config returns sensible defaults when no file exists."""
    config = Config.load(Path("/nonexistent/path/config.toml"))
    assert config.max_depth is None
    assert config.metadata is None
    assert config.icons is None
    assert config.sort_order is None
    assert config.no_color is None
    assert config.no_console is None
    assert config.output_format is None
    assert config.exclude is None


def test_defaults() -> None:
    """Test that Config default values are as expected."""
    config = Config()
    cli_args = CLIArgs().update(config, Namespace())
    assert cli_args.max_depth == 0
    assert cli_args.metadata == []
    assert cli_args.icons == "emoji"
    assert cli_args.sort_order == "files"
    assert cli_args.no_color is False
    assert cli_args.no_console is False
    assert cli_args.output_format == ["text"]
    assert cli_args.exclude == []
    assert cli_args.directory == Path.cwd()


def test_config_load_basic(tmp_path: Path):
    """Test loading a basic config file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
max_depth = 3
icons = "glyphs"
sort_order = "dirs"
no_color = true
""")
    config = Config.load(config_file)
    assert config.max_depth == 3
    assert config.icons == "glyphs"
    assert config.sort_order == "dirs"
    assert config.no_color is True


def test_config_load_metadata_list(tmp_path: Path):
    """Test loading metadata as a list."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
metadata = ["size", "modified"]
""")
    config = Config.load(config_file)
    assert config.metadata == ["size", "modified"]


def test_config_load_metadata_all(tmp_path: Path):
    """Test that metadata 'all' expands to all options."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
metadata = ["all"]
""")
    config = Config.load(config_file)
    cli_args = CLIArgs().update(config, Namespace())
    assert cli_args.metadata == ALL_METADATA


def test_config_load_exclude_patterns(tmp_path: Path):
    """Test loading exclude patterns from dedicated section."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
exclude = ["node_modules", "__pycache__", ".git"]
""")
    config = Config.load(config_file)
    assert config.exclude is not None
    assert "node_modules" in config.exclude
    assert "__pycache__" in config.exclude
    assert ".git" in config.exclude


def test_config_invalid_toml(tmp_path: Path):
    """Test that invalid TOML returns defaults."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("this is not valid toml {{{")
    config = Config.load(config_file)
    cli_args = CLIArgs().update(config, Namespace())
    assert cli_args.max_depth == 0  # Should get defaults


def test_args_cli_overrides_config(tmp_path: Path):
    """Test that CLI args override config values."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
depth = 5
icons = "glyphs"
""")
    config = Config.load(config_file)
    args = get_args(["--depth", "2", "--icons", "plain", str(tmp_path)], config=config)
    assert args.max_depth == 2  # CLI wins
    assert args.icons == "plain"  # CLI wins


def test_args_uses_config_when_not_specified(tmp_path: Path):
    """Test that config values are used when CLI args not provided."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
max_depth = 4
icons = "glyphs"
metadata = ["size"]
""")
    config = Config.load(config_file)
    args = get_args([str(tmp_path)], config=config)
    assert args.max_depth == 4
    assert args.icons == "glyphs"
    assert args.metadata == ["size"]


def test_invalid_config_names(tmp_path: Path):
    """Test that invalid config names are ignored."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
depth = 4
adventure = "glyphs"
meta = ["size"]
""")
    config = Config.load(config_file)
    args = get_args([str(tmp_path)], config=config)
    assert args.max_depth == 0
    assert args.icons == "emoji"
    assert args.metadata == []


def test_args_exclude_merges_config_and_cli(tmp_path: Path):
    """Test that exclude patterns from config and CLI are merged."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[defaults]
exclude = ["node_modules", ".git"]
""")
    config = Config.load(config_file)
    args = get_args(["--exclude", "dist", "build", str(tmp_path)], config=config)
    assert "node_modules" in args.exclude
    assert ".git" in args.exclude
    assert "dist" in args.exclude
    assert "build" in args.exclude
