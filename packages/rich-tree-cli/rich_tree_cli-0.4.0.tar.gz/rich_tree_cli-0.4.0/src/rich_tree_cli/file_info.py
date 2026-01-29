"""A dataclass to hold file metadata information."""

from __future__ import annotations

from functools import cached_property
import hashlib
from os.path import relpath
from pathlib import Path
from typing import TYPE_CHECKING

from bear_epoch_time import EpochTimestamp

from .constants import DAY, DAY_TO_HOURS, DAY_TO_MIN, IS_BINARY, KILOBYTES, MEGABYTES, MONTH, OS, SECONDS, WEEK, YEAR

if TYPE_CHECKING:
    from os import PathLike, stat_result

    from .export.icons import IconManager

now = EpochTimestamp()

type StrPath = str | Path | PathLike


def age_convert(age: float) -> str:
    """Incoming age is in days."""
    if age < (1 / DAY_TO_MIN):
        seconds = int(age * SECONDS)
        return f"{seconds}s"
    if age < (1 / DAY_TO_HOURS):
        minutes = int(age * DAY_TO_MIN)
        return f"{minutes}m"
    if age < DAY:
        hours = int(age * DAY_TO_HOURS)
        return f"{hours}h"
    if age < WEEK:
        days = int(age)
        return f"{days}d"
    if age < MONTH:
        weeks = int(age / WEEK)
        return f"{weeks}w"
    if age < YEAR:
        months = int(age / MONTH)
        return f"{months}Mo"
    years = int(age / YEAR)
    return f"{years}y"


def get_file_hash(path: Path) -> str:
    """Get a simple SHA256 hash of a file - fast and good enough for change detection.

    Args:
        path: Path to the file to hash

    Returns:
        str: Hex digest of the file contents, or empty string if file doesn't exist
    """
    try:
        return hashlib.sha256(path.read_bytes(), usedforsecurity=False).hexdigest()
    except Exception:
        return ""  # File read error, treat as "no file"


def get_platform() -> OS:
    """Get the current operating system platform."""
    import sys  # noqa: PLC0415

    platform_str: str = sys.platform.lower()
    if platform_str.startswith("win"):
        return OS.WINDOWS
    if platform_str.startswith("linux"):
        return OS.LINUX
    if platform_str.startswith("darwin"):
        return OS.DARWIN
    return OS.UNKNOWN


class PathObj(Path):
    """Path subclass to hold file metadata information."""

    def __init__(self, path: StrPath) -> None:
        """Initialize PathObj with a Path object."""
        self.path: Path = Path(path)
        self._ignored: bool = False
        self._modified_str: str | None = None
        self._created_str: str | None = None

    def __fspath__(self) -> str:
        """Return the file system path representation."""
        return str(self.path)

    @property
    def ignored(self) -> bool:
        """Get the ignored status of the file."""
        return self._ignored

    @ignored.setter
    def ignored(self, value: bool) -> None:
        """Set the ignored status of the file."""
        self._ignored = value

    @property
    def _raw_paths(self) -> tuple[str, ...]:
        """Get the raw paths from the underlying Path object."""
        return self.path._raw_paths  # type: ignore[attr-defined]

    @property
    def _str(self) -> str:
        """Get the string representation of the underlying Path object."""
        return str(self.path)

    @_str.setter
    def _str(self, value: str) -> None:
        """Set the string representation of the underlying Path object."""
        self.path = Path(value)

    @property
    def name(self) -> str:
        """Get the file name."""
        return self.path.name

    @property
    def ext(self) -> str:
        """Get the file extension."""
        return self.path.suffix.lstrip(".")

    @cached_property
    def does_exist(self) -> bool:
        """Check if the file exists."""
        return self.exists()

    def exists(self, *, follow_symlinks: bool = False) -> bool:
        """Check if the file exists."""
        return self.path.exists(follow_symlinks=follow_symlinks)

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        """Check if the path is a file."""
        return self.path.is_file(follow_symlinks=follow_symlinks) if self.does_exist else False

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        """Check if the path is a directory."""
        return self.path.is_dir(follow_symlinks=follow_symlinks) if self.does_exist else False

    def resolve(self, strict: bool = False) -> Path:
        """Resolve the path to its absolute form."""
        return self.path.resolve(strict=strict)

    @cached_property
    def file_hash(self) -> str:
        """Get the SHA256 hash of the file."""
        if not self.does_exist or not self.is_file():
            return ""
        return get_file_hash(self.path)

    @cached_property
    def is_binary(self) -> bool:
        """Check if the file is binary by attempting to read it as text."""
        if not self.is_file():
            return False
        try:
            self.path.read_text(encoding="utf-8")
            return False
        except UnicodeDecodeError:
            return True

    def is_symlink(self) -> bool:
        """Check if the path is a symbolic link."""
        return self.path.is_symlink() if self.does_exist else False

    @cached_property
    def get_stat(self) -> stat_result | None:  # type: ignore[override]
        """Get the file's stat result."""
        if not self.does_exist:
            return None
        return self.path.stat()

    @cached_property
    def size(self) -> int:
        """Get the file size in bytes."""
        return self.get_stat.st_size if self.get_stat is not None else 0

    @cached_property
    def length(self) -> int:
        """Get the number of lines in the file."""
        if not self.does_exist or not self.is_file():
            return 0
        if self.is_binary:
            return IS_BINARY
        return len(self.path.read_text(encoding="utf-8").splitlines())

    @cached_property
    def length_str(self) -> str:
        """Get a human-readable string for the number of lines in the file."""
        if self.length == IS_BINARY:
            return "binary"
        return f"{self.length} lines"

    @cached_property
    def size_kb(self) -> float:
        """Get the file size in kilobytes."""
        return (self.size / KILOBYTES) if self.get_stat is not None else 0.0

    @cached_property
    def size_mb(self) -> float:
        """Get the file size in megabytes."""
        return (self.size / MEGABYTES) if self.get_stat is not None else 0.0

    @cached_property
    def size_str(self) -> str:
        """Get a human-readable file size string."""
        if self.size >= MEGABYTES:
            return f"{self.size_mb:.2f} MB"
        if self.size >= KILOBYTES:
            return f"{self.size_kb:.2f} KB"
        return f"{self.size} bytes"

    @cached_property
    def created(self) -> EpochTimestamp | None:
        """Get the file creation time as a timestamp."""
        platform: OS = get_platform()

        if platform is OS.DARWIN and hasattr(self.get_stat, "st_birthtime"):
            value: float | None = getattr(self.get_stat, "st_birthtime", None)
            return EpochTimestamp(int(value or 0) * 1000)
        if platform is OS.WINDOWS and self.get_stat is not None:
            return EpochTimestamp(int(self.get_stat.st_ctime) * 1000)
        return EpochTimestamp(int(self.get_stat.st_mtime) * 1000) if self.get_stat is not None else None

    @cached_property
    def modified(self) -> EpochTimestamp | None:
        """Get the file modification time as a timestamp."""
        return EpochTimestamp(int(self.get_stat.st_mtime) * 1000) if self.get_stat is not None else None

    def created_str(self, datefmt: str, duration: bool) -> str:
        """Get a human-readable string for the creation time."""
        if self.created is None:
            return ""
        if self._created_str is None:
            if duration:
                days: float = self.created.time_since(now, "d")
                self._created_str = f"{age_convert(days)} ago"
            else:
                self._created_str = self.created.to_string(datefmt)
        return self._created_str

    def modified_str(self, datefmt: str, duration: bool) -> str:
        """Get a human-readable string for the modification time."""
        if self.modified is None:
            return ""
        if self._modified_str is None:
            if duration:
                days: float = self.modified.time_since(now, "d")
                self._modified_str = f"{age_convert(days)} ago"
            else:
                self._modified_str = self.modified.to_string(datefmt)
        return self._modified_str

    @cached_property
    def symlink_path(self) -> Path | None:
        """Get the target path of the symlink, if applicable."""
        if self.is_symlink():
            target: Path = self.path.resolve()
            try:
                rel_target: str = relpath(target, self.path.parent)
                return Path(rel_target)
            except (ValueError, OSError):
                return target
        return None

    def to_string(self, icon: IconManager, metadata: list[str], datefmt: str, duration: bool) -> str:
        """Generate a string representation of the file with its metadata.

        Args:
            icon: IconManager to get the file icon
            metadata: List of metadata fields to include (size, lines, created, modified)

        Returns:
            str: String representation of the file
        """
        icon_str: str = icon.get(self.path, is_symlink=self.is_symlink(), is_dir=self.is_dir())
        file_string: str = f"{icon_str} {self.name}"
        if self.is_dir():
            return file_string
        if self.is_symlink():
            file_string += f" -> {self.symlink_path}"
        if self.is_binary:
            file_string += " (binary)"
            return file_string
        if not metadata or self.is_symlink():
            return file_string

        meta_parts: list[str] = []
        if "size" in metadata:
            meta_parts.append(self.size_str)
        if "lines" in metadata:
            meta_parts.append(self.length_str)
        if "created" in metadata and self.created:
            meta_parts.append(self.created_str(datefmt, duration))
        if "modified" in metadata and self.modified:
            meta_parts.append(self.modified_str(datefmt, duration))

        if meta_parts:
            file_string += f" | {' | '.join(meta_parts)}"
        return file_string

    def __bool__(self) -> bool:
        """Boolean representation of PathObj based on path existence."""
        return self.does_exist
