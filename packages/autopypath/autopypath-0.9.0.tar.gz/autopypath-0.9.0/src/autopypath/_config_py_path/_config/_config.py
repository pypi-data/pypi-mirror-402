"""Base class for python path sources"""
# ruff: noqa: E501

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Optional, Union

from ... import _validate
from ..._load_strategy import _LoadStrategy
from ..._log import _log
from ..._marker_type import _MarkerType
from ..._path_resolution import _PathResolution
from ..._types import LoadStrategyLiterals, PathResolutionLiterals, RepoMarkerLiterals

__all__ = []


class NotPresent:
    """Sentinel class to represent a value that is not present."""


NOT_PRESENT = NotPresent()


class _Config:
    """Base configuration class for python path sources.


    :property repo_markers: Mapping of repository markers to their MarkerType.
    :property paths: Additional paths to include in :data:`sys.path`.
    :property load_strategy: The load strategy for handling multiple :data:`sys.path` sources.
    :property path_resolution_order: The order in which to resolve :data:`sys.path` sources.
    """

    __slots__ = ('_repo_markers', '_paths', '_load_strategy', '_path_resolution_order')

    def __init__(
        self,
        *,
        repo_markers: Optional[Mapping[str, Union[_MarkerType, RepoMarkerLiterals]]] = None,
        paths: Optional[Sequence[Union[Path, str]]] = None,
        load_strategy: Optional[Union[_LoadStrategy, LoadStrategyLiterals]] = None,
        path_resolution_order: Optional[Sequence[Union[_PathResolution, PathResolutionLiterals]]] = None,
        strict: bool = False,
    ) -> None:
        """
        :param Mapping[str, MarkerType | Literal['dir', 'file']] | None repo_markers: Markers to identify the repository root.
            Mapping of file or directory names to their MarkerType.

        :param Sequence[Path | str] | None paths: Additional paths to include in :data:`sys.path`.
            Sequence of paths relative to the repository root to be added to :data:`sys.path`.

        :param LoadStrategy | Literal['prepend', 'prepend_highest_priority', 'replace'] | None load_strategy: The
            strategy for loading :func:`sys.path` sources.

            It is expected to be one of `prepend`, `prepend_highest_priority`, or `replace` (as defined
            in :class:`LoadStrategy`). It can use either the enum value or its string representation.

        :param Sequence[PathResolution | Literal['manual', 'autopypath', 'pyproject']]] | None path_resolution_order: The order in which to
            resolve :func:`sys.path` sources.

            It is expected to be a sequence containing any of the following values:
            `manual`, `autopypath`, `pyproject` as defined in :class:`PathResolution`.
            It can use either the enum values or their string representations.
        :param bool strict: (default: ``False``) Indicates whether strict mode is enabled for error handling.
        """
        self._repo_markers: Union[MappingProxyType[str, _MarkerType], None] = _validate.repo_markers(repo_markers)
        self._paths: Union[tuple[Path, ...], None] = _validate.paths(paths)
        self._load_strategy: Union[_LoadStrategy, None] = _validate.load_strategy(load_strategy)
        self._path_resolution_order: Union[tuple[_PathResolution, ...], None] = _validate.path_resolution_order(
            path_resolution_order
        )

        cls = self.__class__.__name__
        _log.debug(
            f'{cls} initialized with repo_markers={self._repo_markers}, '
            f'paths={self.paths}, load_strategy={self.load_strategy}, '
            f'path_resolution_order={self.path_resolution_order}'
        )

    @property
    def repo_markers(self) -> Union[MappingProxyType[str, _MarkerType], None]:
        """Mapping of repository markers to their MarkerType.

        :return MappingProxyType[str, MarkerType] | None: A mapping where keys are filenames or directory names
            that indicate the repository root, and values are of type `MarkerType`.
            ``None`` if no custom repo markers are set.
        """
        return self._repo_markers

    @property
    def load_strategy(self) -> Union[_LoadStrategy, None]:
        """The load strategy for handling multiple :func:`sys.path` sources.

        :return LoadStrategy | None: The strategy used when handling multiple sys.path sources.
            ``None`` if no custom load strategy is set.
        """
        return self._load_strategy

    @property
    def path_resolution_order(self) -> Union[tuple[_PathResolution, ...], None]:
        """The order in which to resolve :func:`sys.path` sources.

        :return tuple[PathResolution, ...] | None: A tuple defining the order of resolution for sys.path sources.
            ``None`` if no custom resolution order is set.
        """
        return self._path_resolution_order

    @property
    def paths(self) -> Union[tuple[Path, ...], None]:
        """Additional paths to include in :data:`sys.path`.

        :return tuple[Path, ...] | None: A tuple of additional paths relative to the repository root
            to be added to :data:`sys.path`. ``None`` if no additional paths are set.
        """
        return self._paths

    def __repr__(self) -> str:
        """String representation of the Config object.

        :return str: A string representation of the Config instance.
        """
        cls = self.__class__.__name__

        paths_list: list[str] = []
        if self.paths is not None:
            for path in self.paths:
                paths_list.append(f'{str(path)!r}')
            path_repr = '[' + ', '.join(paths_list) + ']'
        else:
            path_repr = 'None'

        markers_list: list[str] = []
        if self.repo_markers is not None:
            for key, value in self.repo_markers.items():
                marker_str = f'_MarkerType.{value.name}'
                markers_list.append(f'{key!r}: {marker_str}')
            markers_repr = '{' + ', '.join(markers_list) + '}'
        else:
            markers_repr = 'None'

        path_resolution_list: list[str] = []
        if self.path_resolution_order is not None:
            for order in self.path_resolution_order:
                path_resolution_list.append(f'_PathResolution.{order.name}')
            path_resolution_repr = '[' + ', '.join(path_resolution_list) + ']'
        else:
            path_resolution_repr = 'None'

        load_strategy_repr = f'_LoadStrategy.{self.load_strategy.name}' if self.load_strategy is not None else 'None'

        return (
            f'{cls}(repo_markers={markers_repr}, '
            f'paths={path_repr}, load_strategy={load_strategy_repr}, '
            f'path_resolution_order={path_resolution_repr})'
        )

    def __eq__(self, other: object) -> bool:
        """Equality comparison for Config objects.

        :param object other: Another object to compare with.
        :return bool: True if both Config instances are equal, False otherwise.
        """
        if not isinstance(other, _Config):
            return NotImplemented
        return (
            self.repo_markers == other.repo_markers
            and self.paths == other.paths
            and self.load_strategy == other.load_strategy
            and self.path_resolution_order == other.path_resolution_order
        )

    def __hash__(self) -> int:
        """Hash for Config objects."""
        repo_markers: MappingProxyType[str, _MarkerType] = self.repo_markers or MappingProxyType({})
        return hash(
            (frozenset(sorted(repo_markers.items())), self.paths, self.load_strategy, self.path_resolution_order)
        )

    def replace(
        self,
        *,
        repo_markers: Union[Mapping[str, Union[_MarkerType, RepoMarkerLiterals]], None, NotPresent] = NOT_PRESENT,
        paths: Union[Sequence[Union[Path, str]], None, NotPresent] = NOT_PRESENT,
        load_strategy: Union[_LoadStrategy, LoadStrategyLiterals, None, NotPresent] = NOT_PRESENT,
        path_resolution_order: Union[
            Sequence[Union[_PathResolution, PathResolutionLiterals]], None, NotPresent
        ] = NOT_PRESENT,
    ) -> '_Config':
        """Creates a copy of the current Config instance with specified attributes replaced.

        If an attribute is not provided, the value from the current instance is used.

        The default value for each parameter is a sentinel `NotPresent` instance,
        which indicates that the current value should be retained.

        :param Mapping[str, MarkerType] | None | NotPresent repo_markers: New repo_markers value.
        :param Sequence[Path | str] | None | NotPresent paths: New paths value.
        :param LoadStrategy | str | None | NotPresent load_strategy: New load_strategy value.
        :param Sequence[PathResolution | str] | None | NotPresent path_resolution_order: New path_resolution_order
            value.

        :return Config: A new Config instance with selected attributes replaced.
        """

        new_repo_markers = self.repo_markers if isinstance(repo_markers, NotPresent) else repo_markers
        new_paths = self.paths if isinstance(paths, NotPresent) else paths
        new_load_strategy = self.load_strategy if isinstance(load_strategy, NotPresent) else load_strategy
        new_path_resolution_order = (
            self.path_resolution_order if isinstance(path_resolution_order, NotPresent) else path_resolution_order
        )
        return _Config(
            repo_markers=new_repo_markers,
            paths=new_paths,
            load_strategy=new_load_strategy,
            path_resolution_order=new_path_resolution_order,
        )
