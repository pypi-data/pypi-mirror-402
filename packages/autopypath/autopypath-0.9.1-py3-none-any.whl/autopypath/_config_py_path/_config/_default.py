"""Default config instance for autopypath."""

from pathlib import Path
from types import MappingProxyType

from ... import _defaults
from ..._load_strategy import _LoadStrategy
from ..._log import _log
from ..._marker_type import _MarkerType
from ..._path_resolution import _PathResolution
from ._config import _Config


class _DefaultConfig(_Config):
    """Default configuration for autopypath."""

    def __init__(self, *, strict: bool = False) -> None:
        """Default configuration for autopypath.

        The default configuration uses the default values defined in
        :mod:`autopypath.defaults`. It validates that these defaults are not None
        or empty where applicable and initializes the class with these default values.
        :raises AutopypathError: If any of the default values are None or empty where not allowed.
        """

        _log.debug('Initializing DefaultConfig with default values from autopypath.defaults')

        # Override types for slots because they are guaranteed to be non-None/non-empty
        # from the DefaultConfig module because we double check them above.
        # This let us avoid mypy errors about possible None values when accessing the
        # the default properties.
        self._load_strategy: _LoadStrategy  # type: ignore
        self._paths: tuple[Path, ...]  # type: ignore
        self._repo_markers: MappingProxyType[str, _MarkerType]  # type: ignore
        self._path_resolution_order: tuple[_PathResolution, ...]  # type: ignore

        super().__init__(
            repo_markers=_defaults._REPO_MARKERS,
            paths=_defaults._PATHS,
            load_strategy=_defaults._LOAD_STRATEGY,
            path_resolution_order=_defaults._PATH_RESOLUTION_ORDER,
        )

    @property
    def repo_markers(self) -> MappingProxyType[str, _MarkerType]:
        """Mapping of repository markers to their MarkerType.

        :return MappingProxyType[str, MarkerType] | None: A mapping where keys are filenames or directory names
            that indicate the repository root, and values are of type `MarkerType`.
            ``None`` if no custom repo markers are set.
        """
        return self._repo_markers

    @property
    def load_strategy(self) -> _LoadStrategy:
        """The load strategy for handling multiple :data:`sys.path` sources.

        :return LoadStrategy | None: The strategy used when handling multiple sys.path sources.
            ``None`` if no custom load strategy is set.
        """
        return self._load_strategy

    @property
    def path_resolution_order(self) -> tuple[_PathResolution, ...]:
        """The order in which to resolve :data:`sys.path` sources.

        :return tuple[PathResolution, ...] | None: A tuple defining the order of resolution for sys.path sources.
            ``None`` if no custom resolution order is set.
        """
        return self._path_resolution_order

    @property
    def paths(self) -> tuple[Path, ...]:
        """Additional paths to include in :data:`sys.path`.

        :return tuple[Path, ...] | None: A tuple of additional paths relative to the repository root
            to be added to :data:`sys.path`. ``None`` if no additional paths are set.
        """
        return self._paths

    def __repr__(self) -> str:
        """String representation of the DefaultConfig object.

        :return str: A string representation of the DefaultConfig instance.
        """
        return (
            f'{self.__class__.__name__}()\n'
            f'#  repo_markers={self.repo_markers!r}\n'
            f'#  paths={self.paths!r}\n'
            f'#  load_strategy={self.load_strategy!r}\n'
            f'#  path_resolution_order={self.path_resolution_order!r}'
        )
