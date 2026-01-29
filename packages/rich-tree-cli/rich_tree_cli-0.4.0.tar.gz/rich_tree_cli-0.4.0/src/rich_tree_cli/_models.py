from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Final, NamedTuple, NoReturn, Self

from .file_info import PathObj

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from pathspec import PathSpec
    from rich.tree import Tree


class ImmutableList(list):
    """An immutable list that prevents modification."""

    def _immutable(self, *args, **kwargs) -> NoReturn:  # noqa: ARG002
        raise TypeError("This list is immutable and cannot be modified.")

    __setitem__: Callable[..., NoReturn] = _immutable
    __delitem__: Callable[..., NoReturn] = _immutable
    append: Callable[..., NoReturn] = _immutable
    extend: Callable[..., NoReturn] = _immutable
    insert: Callable[..., NoReturn] = _immutable
    remove: Callable[..., NoReturn] = _immutable
    pop: Callable[..., NoReturn] = _immutable
    clear: Callable[..., NoReturn] = _immutable

    def __bool__(self) -> bool:
        return False

    def __len__(self) -> int:
        return 0

    def __hash__(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        return hash("ImmutableList")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, list):
            return False
        return list(self) == other

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


EMPTY_LIST: Final[ImmutableList] = ImmutableList()


class DummyObject:
    """A dummy object that mimics a container with no paths."""

    @property
    def paths(self) -> ImmutableList:
        """Return an empty list."""
        return EMPTY_LIST


PATH_NOT_FOUND = DummyObject()


def path_parser(path: Path, spec: PathSpec) -> PathObj:
    """We will need to run this through the threadpool so we need individual tasks.

    Args:
        path: The file or directory to parse, passed in via threadpool
        cls: The PathsContainer class
        spec: The PathSpec object for ignore patterns
    """
    obj = PathObj(path=path)
    obj.ignored = spec.match_file(str(path))
    return obj


def key_by(x: PathObj, key: str = "modified") -> int:
    """Key function to sort PathObjects by modified time.

    Args:
        x: The PathObj to extract the key from
        key: The attribute name to use as the key (default is "modified")
    """
    return getattr(x, key)


@dataclass(slots=True)
class CachedContainer:
    """Pre-cached container for non-ignored PathObj objects."""

    paths: list[PathObj] = field(default_factory=list)
    mem_check: set[PathObj] = field(default_factory=set)

    def add(self, file_info: PathObj) -> None:
        """Add a PathObj to the cached container if not already present.

        Args:
            file_info: The PathObj object to add
        """
        if file_info not in self.mem_check:
            self.paths.append(file_info)
            self.mem_check.add(file_info)

    def __iter__(self) -> Iterator[PathObj]:
        """Iterator over the cached paths."""
        return iter(self.paths)

    def __contains__(self, item: PathObj) -> bool:
        """Check if a PathObj is in the cached container."""
        return item in self.mem_check

    def __len__(self) -> int:
        """Get the number of PathObj objects in the cached container."""
        return len(self.paths)


@dataclass
class PathsContainer:
    """Container for multiple PathContainer objects."""

    root: Path = Path(".")
    cached_paths: defaultdict[Path, CachedContainer] = field(default_factory=lambda: defaultdict(CachedContainer))

    sort_order: str = "files"

    def get_items(self, path: Path) -> list[PathObj]:
        """Get items in the directory, sorted by the specified order."""
        container: CachedContainer | DummyObject = self.cached_paths.get(path, PATH_NOT_FOUND)
        return container.paths

    @cached_property
    def count_files(self) -> int:
        """Number of files that were processed."""
        return sum(len(container) for container in self.cached_paths.values())

    @cached_property
    def count_dirs(self) -> int:
        """Number of directories that were processed."""
        return len(self.cached_paths)

    @cached_property
    def non_ignored_paths(self) -> list[Path]:
        """List of non-ignored file paths."""
        return [obj.path for obj in self.cached_paths.values() for obj in obj]

    @cached_property
    def membership_set(self) -> set[str]:
        """Set of non-ignored file paths as strings for fast membership testing."""
        return {str(obj) for obj in self.cached_paths.values() for obj in obj}

    def __contains__(self, item: str) -> bool:
        """Check if a path string is in the non-ignored paths."""
        return item in self.membership_set

    def __len__(self) -> int:
        """Get the total number of non-ignored paths."""
        return self.count_files + self.count_dirs

    @classmethod
    def create(
        cls,
        root_path: Path | str,
        spec: PathSpec,
        sort_order: str = "files",
    ) -> PathsContainer:
        """Create a PathsContainer from a directory and a PathSpec."""
        new: Self = cls(sort_order=sort_order)
        new.root = Path(root_path).expanduser().resolve()
        new.cached_paths[new.root.parent].add(PathObj(new.root))
        for root, dirs, files in new.root.walk():
            for filename in files:
                path: Path = Path(root) / filename
                obj: PathObj = path_parser(path, spec)
                if obj.ignored:
                    continue
                new.cached_paths[path.parent].add(obj)
            for dirname in list(dirs):
                dir_path: Path = Path(root) / dirname
                is_dir_ignored: bool = spec.match_file(str(dir_path.relative_to(new.root)) + "/")
                if is_dir_ignored:
                    dirs.remove(dirname)
                else:
                    obj = PathObj(dir_path)
                    new.cached_paths[dir_path.parent].add(obj)
        for container in new.cached_paths.values():
            container.paths.sort(
                key=lambda x: (x.is_dir(), x.name.lower())
                if sort_order == "files"
                else (not x.is_dir(), x.name.lower())
            )
        return new


# fmt: off
class DataResult(NamedTuple):
    """Data returned from :class:`RichTreeCLI.run`."""

    tree: Tree                             # The rich Tree object representing the directory structure
    root: Path                             # The root path of the directory being analyzed
    sort_order: str                        # The sort order used for displaying files and directories
    max_depth: int                         # The maximum depth of the directory tree
    dir_count: int                         # The total number of directories processed
    file_count: int                        # The total number of files processed
    totals: str                            # A summary string of totals (e.g., total files and directories)
    cached_paths: PathsContainer           # Container for cached paths

class NullConsole:
    """A console that does nothing, used when no console output is desired."""

    def print(self, *args, **kwargs) -> None:
        pass
