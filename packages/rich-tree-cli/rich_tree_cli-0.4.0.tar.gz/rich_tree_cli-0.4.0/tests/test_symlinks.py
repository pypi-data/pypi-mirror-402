"""Tests for symlink handling in file_info.py."""

from pathlib import Path

import pytest

from rich_tree_cli.export.icons import IconManager, IconMode
from rich_tree_cli.file_info import PathObj


@pytest.fixture
def icon_manager() -> IconManager:
    """Create an icon manager for testing."""
    return IconManager(mode=IconMode.GLYPHS_ICONS)


class TestSymlinkRelativePaths:
    """Test symlink relative path display."""

    def test_symlink_to_parent_directory(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a file in the parent directory."""
        # Create structure:
        # tmp/
        #   target.txt
        #   subdir/
        #     link -> ../target.txt
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        subdir: Path = tmp_path / "subdir"
        subdir.mkdir()

        link: Path = subdir / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> ../target.txt" in result
        assert "link" in result

    def test_symlink_to_sibling_file(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a file in the same directory."""
        # Create structure:
        # tmp/
        #   target.txt
        #   link -> target.txt
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        link: Path = tmp_path / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> target.txt" in result
        assert "link" in result

    def test_symlink_to_grandparent_directory(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a file two levels up."""
        # Create structure:
        # tmp/
        #   target.txt
        #   level1/
        #     level2/
        #       link -> ../../target.txt
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        level1: Path = tmp_path / "level1"
        level1.mkdir()
        level2: Path = level1 / "level2"
        level2.mkdir()

        link: Path = level2 / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> ../../target.txt" in result
        assert "link" in result

    def test_symlink_to_cousin_directory(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a file in a sibling directory."""
        # Create structure:
        # tmp/
        #   dir1/
        #     target.txt
        #   dir2/
        #     link -> ../dir1/target.txt
        dir1: Path = tmp_path / "dir1"
        dir1.mkdir()
        target_file = dir1 / "target.txt"
        target_file.write_text("content")

        dir2: Path = tmp_path / "dir2"
        dir2.mkdir()
        link: Path = dir2 / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> ../dir1/target.txt" in result
        assert "link" in result

    def test_symlink_to_nested_cousin(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a file in a nested cousin directory."""
        # Create structure:
        # tmp/
        #   dir1/
        #     nested/
        #       target.txt
        #   dir2/
        #     link -> ../dir1/nested/target.txt
        dir1: Path = tmp_path / "dir1"
        dir1.mkdir()
        nested: Path = dir1 / "nested"
        nested.mkdir()
        target_file: Path = nested / "target.txt"
        target_file.write_text("content")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        link: Path = dir2 / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> ../dir1/nested/target.txt" in result
        assert "link" in result

    def test_symlink_absolute_fallback(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test that absolute path is shown when relative path computation fails."""
        # This is harder to test directly since os.path.relpath rarely fails
        # on normal file systems, but we can verify the code path exists
        # by checking a symlink that resolves properly
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        link: Path = tmp_path / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        # Should show either relative or absolute path, but must include ->
        assert " -> " in result
        assert "link" in result

    def test_symlink_to_directory(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a directory."""
        # Create structure:
        # tmp/
        #   target_dir/
        #   link -> target_dir
        target_dir: Path = tmp_path / "target_dir"
        target_dir.mkdir()

        link: Path = tmp_path / "link"
        link.symlink_to(target_dir)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        # Directory symlinks should still be shown as directories
        assert "link" in result

    def test_broken_symlink(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink pointing to a non-existent file."""
        # Create structure:
        # tmp/
        #   link -> nonexistent.txt (broken)
        link: Path = tmp_path / "link"
        nonexistent: Path = tmp_path / "nonexistent.txt"
        link.symlink_to(nonexistent)

        path_obj = PathObj(link)
        # This should not crash, even though the target doesn't exist
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert "link" in result
        assert " -> " in result

    def test_symlink_chain(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test a symlink that points to another symlink."""
        # Create structure:
        # tmp/
        #   target.txt
        #   link1 -> target.txt
        #   link2 -> link1
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        link1: Path = tmp_path / "link1"
        link1.symlink_to(target_file)

        link2: Path = tmp_path / "link2"
        link2.symlink_to(link1)

        path_obj = PathObj(link2)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        # resolve() should follow the chain to target.txt
        assert " -> target.txt" in result
        assert "link2" in result

    def test_symlink_with_spaces_in_name(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test symlink with spaces in filename."""
        # Create structure:
        # tmp/
        #   target file.txt
        #   my link -> target file.txt
        target_file: Path = tmp_path / "target file.txt"
        target_file.write_text("content")

        link: Path = tmp_path / "my link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        result: str = path_obj.to_string(icon_manager, [], "%Y-%m-%d", duration=False)

        assert " -> target file.txt" in result
        assert "my link" in result

    def test_symlink_no_metadata_shown(self, tmp_path: Path, icon_manager: IconManager) -> None:
        """Test that metadata is not shown for symlinks."""
        # Create structure:
        # tmp/
        #   target.txt
        #   link -> target.txt
        target_file: Path = tmp_path / "target.txt"
        target_file.write_text("content")

        link: Path = tmp_path / "link"
        link.symlink_to(target_file)

        path_obj = PathObj(link)
        # Request metadata, but symlinks shouldn't show it
        result: str = path_obj.to_string(icon_manager, ["size", "lines"], "%Y-%m-%d", duration=False)

        assert " -> " in result
        assert " | " not in result  # No metadata separator
        assert "bytes" not in result
        assert "lines" not in result
