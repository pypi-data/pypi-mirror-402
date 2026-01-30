"""Module to configure Python path."""
# ruff: noqa: E501

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional, Union

from .. import _validate
from .._exceptions import AutopypathError
from .._load_strategy import _LoadStrategy
from .._log import _log
from .._marker_type import _MarkerType
from .._path_resolution import _PathResolution
from .._types import LoadStrategyLiterals, PathResolutionLiterals, RepoMarkerLiterals
from ._config import _AutopypathConfig, _DefaultConfig, _ManualConfig, _PyProjectConfig

__all__ = []

_EMPTY_AUTOPYPATH_CONFIG: _AutopypathConfig = _AutopypathConfig(None)
"""An empty AutopypathConfig instance used when no autopypath.toml is found."""

_NON_RESOLVABLE_SYS_PATH: str = 'non-resolvable sys.path entry found'
"""Log message prefix for non-resolvable sys.path entries."""

_NON_RESOLVABLE_PATH: str = 'non-resolvable configured path found'
"""Log message prefix for non-resolvable configured paths."""


class _ConfigPyPath:
    """Configures :data:`sys.path` based on manual settings, pyproject.toml, and autopypath.toml."""

    __slots__ = (
        '_context_file',
        '_repo_root_path',
        '_manual',
        '_pyproject',
        '_autopypath',
        '_default',
        '_path_resolution_order',
        '_load_strategy',
        '_paths',
        '_original_sys_path',
        '_updated_paths',
        '_dry_run',
        '_strict',
        '_log_level',
    )

    def __init__(
        self,
        *,
        context_file: Union[Path, str],
        repo_markers: Optional[Mapping[str, RepoMarkerLiterals]] = None,
        paths: Optional[Sequence[Union[Path, str]]] = None,
        load_strategy: Optional[LoadStrategyLiterals] = None,
        path_resolution_order: Optional[Sequence[PathResolutionLiterals]] = None,
        dry_run: bool = False,
        strict: bool = False,
        log_level: Optional[int] = None,
    ) -> None:
        """Configures :data:`sys.path` based on manual settings, autopypath.toml, and pyproject.toml.

        Usage
        -----
        This is the internal function used by autopypath to set up the Python path.

        It is typically called automatically when the module is imported,
        but can also be called manually to customize behavior.

        It is very liberal in what it accepts, but will raise `AutopypathError` or
        `AutopypathError` if the inputs are invalid.

        :param Path | str context_file: The file path of the script that is configuring the Python path.
            If passed as a string, it must be passed as a POSIX-style relative path (e.g., "src/main.py").
            If passed as a Path, it can be either absolute or relative.
        :param Mapping[str, MarkerType | Literal['dir', 'file']] | None repo_markers: (default: ``None``) A
            dictionary where keys are filenames or directory names that indicate the repository root.
            The values should be `file` or `dir`. It is case-sensitive.

            If ``None``, defaults to :var:`~autopypath.defaults.REPO_MARKERS`.

        :param Sequence[Path | str] | None paths: (default: ``None``) A list of Path objects or strings relative to
            the repo root to add to :data:`sys.path`.

            If ``None``, defaults to :var:`~autopypath.defaults.PATHS`.

        :param LoadStrategy | Literal['prepend', 'prepend_highest_priority', 'replace'] | None load_strategy: (default:
            ``None``) The strategy for handling multiple :data:`sys.path` sources.

            It is expected to be `prepend`, `prepend_highest_priority`, or `replace` (as defined
            in :class:`LoadStrategy`). It can use either the enum value or its string representation.

            If ``None``, defaults to :var:`~autopypath.defaults.LOAD_STRATEGY`.

        :param PathResolution | Literal['manual', 'autopypath', 'pyproject'] | None path_resolution_order: (default:
            ``None``) The order in which to resolve :data:`sys.path` sources.

            It is expected to be a sequence containing any of the following values:
            ``manual``, ``autopypath``, ``pyproject`` as defined in :class:`PathResolution`.
            If ``None``, the default order from :var:`~autopypath.defaults.PATH_RESOLUTION_ORDER` is used.

            It can use either the enum values or their string representations.
        :param bool dry_run: (default: ``False``) If ``True``, the configuration is processed but :data:`sys.path` is
            not actually modified. This is useful for testing or inspecting the configuration without making changes.
        :param bool strict: (default: ``False``) If ``True``, raises exceptions on errors during configuration.
            If ``False``, errors are logged as warnings and the configuration continues where possible.
        :param int | None log_level: (default: ``None``) The logging level to set for the internal logger during
            configuration. It will be restored to its original setting afterwards. If ``None``,
            the current log level is used.
        :raises AutopypathError: On any error. This includes but is not limited to:
            - If any of the inputs are of incorrect type.
            - If any of the inputs have invalid values or strict mode is enabled
              and an unknown path resolution source is encountered.
            - If the repository root cannot be found or if strict mode is enabled
              and a configured path cannot be resolved.
        """
        _existing_log_level: int = _log.level
        """Existing log level to restore later."""

        existing_sys_path: list[str] = sys.path.copy()
        """Existing sys.path to restore later if needed."""

        self._dry_run: bool = _validate.dry_run(dry_run)
        """Indicates whether the configuration was a dry run (no actual sys.path modification)."""

        self._strict: bool = _validate.strict(strict)
        """Indicates whether strict mode is enabled for error handling."""

        try:
            _log.setLevel(_validate.log_level(log_level))

            if self.dry_run:
                _log.info('Dry run enabled - sys.path will not actually be modified.')

            self._original_sys_path: list[str] = sys.path.copy()
            """The original sys.path before any modifications."""

            self._context_file: Path = _validate.context_file(context_file)
            """The file path of the script that is configuring the Python path."""

            self._autopypath: Union[_AutopypathConfig, None] = None
            """Configuration loaded from autopypath.toml.

            It is ``None`` if no autopypath.toml file is found during the repo root search.
            """

            self._manual = _ManualConfig(
                repo_markers=repo_markers,
                paths=paths,
                load_strategy=load_strategy,
                path_resolution_order=path_resolution_order,
            )
            """Manual configuration provided directly to the function."""

            self._default = _DefaultConfig()
            """Default autopypath configuration."""

            self._repo_root_path: Path = self._find_repo_root_path(self.context_file)
            """The repository root path based on the configured repo markers."""

            self._pyproject = _PyProjectConfig(self.repo_root_path)
            """Configuration loaded from pyproject.toml (if present)."""

            self._path_resolution_order: tuple[_PathResolution, ...] = self._determine_path_resolution_order()
            """The order in which to resolve :data:`sys.path` sources."""

            self._load_strategy: _LoadStrategy = self._determine_load_strategy()
            """The strategy for handling multiple :data:`sys.path` sources."""

            self._paths: tuple[Path, ...] = self._process_paths()
            """The final resolved paths that will be added to :data:`sys.path`."""

            self._apply_paths(self.paths)

            self._updated_paths: tuple[str, ...] = tuple(sys.path)
            """The updated sys.path after modifications."""
        except BaseException:  # Yes. We want to catch ALL exceptions here.
            # On ANY error, restore original sys.path
            # "First, do no harm"
            sys.path = existing_sys_path
            _log.debug('Error during configuration - sys.path remains unchanged: %s', sys.path)
            raise
        finally:
            _log.setLevel(_existing_log_level)

    def _apply_paths(self, paths: Sequence[Path]) -> None:
        """Applies the resolved paths to :data:`sys.path`.

        Based on the load strategy, it updates :data:`sys.path` accordingly.
        """
        if self.load_strategy not in {  # future-proofing for new strategies that may be added
            _LoadStrategy.REPLACE,
            _LoadStrategy.PREPEND_HIGHEST_PRIORITY,
            _LoadStrategy.PREPEND,
        }:  # pragma: no cover  # should never happen due to earlier validation
            raise AutopypathError(f'Unknown load strategy: {str(self.load_strategy)}')
        if not paths:
            _log.debug('No paths to apply to sys.path.')
            return

        # Note: paths are already resolved and ordered for load strategy in _process_paths
        stringified_paths = [str(p) for p in paths]
        if self.load_strategy == _LoadStrategy.REPLACE:
            if not self.dry_run:
                sys.path = stringified_paths
                _log.debug('sys.path replaced all paths with: %s', stringified_paths)
            else:
                _log.debug('Dry run - sys.path would be replaced with: %s', stringified_paths)
        else:
            if not self.dry_run:
                sys.path = stringified_paths + sys.path
                _log.debug('sys.path updated with strategy %s paths: %s', str(self.load_strategy), stringified_paths)
            else:
                _log.debug(
                    'Dry run - sys.path would be updated with strategy %s paths: %s',
                    str(self.load_strategy),
                    stringified_paths,
                )

    def _process_paths(self) -> tuple[Path, ...]:
        """Determines the final resolved paths and returns them.

        It follows the configured path resolution order and load strategy to
        combine paths from manual settings, pyproject.toml, and autopypath.toml.

        Paths that are already in :data:`sys.path` are not duplicated.

        :return tuple[Path, ...]: The paths to be added to :data:`sys.path`.
        :raises AutopypathError: If a configured path cannot be resolved and strict mode is enabled.
        :raises AutopypathError: If an unknown path resolution source is encountered and strict mode is enabled.
        """

        existing_paths = sys.path if self.load_strategy != _LoadStrategy.REPLACE else []
        known_paths: set[Path] = set()
        for p in existing_paths:
            try:
                _log.debug('Resolving existing sys.path entry: %s', p)
                path_obj = Path(p).resolve(strict=True)
                if path_obj not in known_paths:
                    known_paths.add(path_obj)
            except Exception:
                _log.debug(f'{_NON_RESOLVABLE_SYS_PATH}: %s', p)

        raw_paths: list[Path] = []

        # collect paths based on resolution order and load strategy
        for source in self.path_resolution_order:
            if source == _PathResolution.MANUAL:
                source_paths = self.manual_config.paths
                _log.debug('Resolving paths from MANUAL source: %s', source_paths)
            elif source == _PathResolution.AUTOPYPATH:
                source_paths = self.autopypath_config.paths
                _log.debug('Resolving paths from AUTOPYPATH source: %s', source_paths)
            elif source == _PathResolution.PYPROJECT:
                source_paths = self.pyproject_config.paths
                _log.debug('Resolving paths from PYPROJECT source: %s', source_paths)
            else:  # pragma: no cover  # This is future-proofing for new sources that may be added
                if self._strict:
                    _log.error('Unknown path resolution source: %s', source)
                    raise AutopypathError(f'Unknown path resolution source: {source}')
                _log.warning('Unknown path resolution source: %s', source)
                continue

            # If this source has no paths, skip it
            if not source_paths:
                _log.debug('No paths found from source: %s', source)
                continue

            # Identify load strategy behavior
            if self.load_strategy == _LoadStrategy.REPLACE:
                raw_paths.extend(source_paths)
                _log.debug('Load strategy REPLACE: Using paths %s from %s', source_paths, source)
                break
            elif self.load_strategy == _LoadStrategy.PREPEND_HIGHEST_PRIORITY:
                _log.debug('Load strategy PREPEND_HIGHEST_PRIORITY: Using paths %s from %s', source_paths, source)
                raw_paths = list(source_paths)
                break
            elif self.load_strategy == _LoadStrategy.PREPEND:
                _log.debug('Load strategy PREPEND: Appending paths %s from %s', source_paths, source)
                raw_paths.extend(source_paths)
            else:  # pragma: no cover  # should never happen due to earlier validation
                raise AutopypathError(f'Unknown load strategy: {str(self.load_strategy)}')

        # Process default paths if no paths have been set yet
        if not raw_paths:
            default_paths = self.default_config.paths
            _log.debug('Processing default paths: %s', default_paths)
            for path in default_paths:
                raw_paths.append(path)

        # Remove duplicates while preserving order
        # and resolve paths
        unique_paths: list[Path] = []
        for path in raw_paths:
            try:
                resolved_path = (
                    path.resolve(strict=True)
                    if path.is_absolute()
                    else (self.repo_root_path / path).resolve(strict=True)
                )
            except Exception as exc:
                if self._strict:
                    _log.error('Could not resolve configured path: %s', path)
                    raise AutopypathError(f'Could not resolve configured path: {path}') from exc
                _log.warning('Could not resolve configured path: %s', path)
                continue
            if resolved_path not in known_paths:
                unique_paths.append(resolved_path)
                known_paths.add(resolved_path)

        # Final check for empty paths
        if not unique_paths:
            if self.load_strategy == _LoadStrategy.REPLACE:
                _log.error('No valid paths to use as sys.path after processing in "replace" mode.')
                raise AutopypathError('autopypath: No valid paths to use as sys.path after processing in "replace" mode.')
            _log.warning('autopypath: No valid paths to add to sys.path after processing.')

        _log.debug('Final resolved paths to add to sys.path: %s', unique_paths)
        return tuple(unique_paths)

    def _determine_load_strategy(self) -> _LoadStrategy:
        """Determines the load strategy for handling multiple :data:`sys.path` sources.

        It looks for the strategy in the following precedence:
        1. Manual configuration provided directly to the function.
        2. Configuration loaded from autopypath.toml.
        3. Configuration loaded from pyproject.toml.
        4. Default autopypath configuration.

        The first source that provides a non-None strategy is used.

        :return LoadStrategy: The strategy for handling multiple :data:`sys.path` sources.
        """
        if self.manual_config.load_strategy is not None:
            strategy = _LoadStrategy(self.manual_config.load_strategy)
            _log.debug('Using manual load strategy: %s', strategy)
            return strategy

        if self.autopypath_config.load_strategy is not None:
            strategy = _LoadStrategy(self.autopypath_config.load_strategy)
            _log.debug('Using autopypath.toml load strategy: %s', strategy)
            return strategy

        if self.pyproject_config.load_strategy is not None:
            strategy = _LoadStrategy(self.pyproject_config.load_strategy)
            _log.debug('Using pyproject.toml load strategy: %s', strategy)
            return strategy

        _log.debug('Using default load strategy: %s', self.default_config.load_strategy)
        return self.default_config.load_strategy

    def _determine_path_resolution_order(self) -> tuple[_PathResolution, ...]:
        """Determines the order in which to resolve :data:`sys.path` sources.

        It looks for the order in the following precedence sequence:
        1. Manual configuration provided directly to the function.
        2. Configuration loaded from autopypath.toml.
        3. Configuration loaded from pyproject.toml.
        4. Default autopypath configuration.

        The first source that provides a non-None order is used.

        Note that the path resolution order determines the order in which
        paths are collected from the various sources before applying the load strategy
        not the priority of the sources themselves. The priority of which source's
        path resolution order is selected follows the precedence sequence above
        and only one source's order is used. A path resolution order set manually
        will always take precedence over any other source and so on.

        :return tuple[PathResolution, ...]: The order in which to resolve :data:`sys.path` sources.
        """
        if self.manual_config.path_resolution_order is not None:
            order = tuple(_PathResolution(item) for item in self.manual_config.path_resolution_order)
            _log.debug('Using manual path resolution order: %s', order)
            return order

        if self.autopypath_config.path_resolution_order is not None:
            order = tuple(_PathResolution(item) for item in self.autopypath_config.path_resolution_order)
            _log.debug('Using autopypath.toml path resolution order: %s', order)
            return order

        if self.pyproject_config.path_resolution_order is not None:
            order = tuple(_PathResolution(item) for item in self.pyproject_config.path_resolution_order)
            _log.debug('Using pyproject.toml path resolution order: %s', order)
            return order
        _log.debug('Using default path resolution order: %s', self.default_config.path_resolution_order)
        return self.default_config.path_resolution_order

    def _find_repo_root_path(self, context_file_path: Path) -> Path:
        """Finds the repository root path based on the configured repo markers.

        :param Path context_file_path: The file path of the script that is configuring the Python path.
        :return Path: The path to the repository root.
        :raises AutopypathError: If the repository root cannot be found.
        """
        repo_markers = self.manual_config.repo_markers or self.default_config.repo_markers
        current_path = context_file_path.parent.resolve(strict=True)
        while True:
            autopypath_path = current_path / 'autopypath.toml'
            # load autopypath.toml if found during repo search (but only once)
            if self._autopypath is None and autopypath_path.exists():
                if not autopypath_path.is_file():
                    if self._strict:
                        _log.error(
                            'Found autopypath.toml at %s but it is not a file', autopypath_path.resolve(strict=True)
                        )
                        raise AutopypathError(f'Found autopypath.toml at {autopypath_path} but it is not a file')
                    _log.warning(
                        'Found autopypath.toml at %s but it is not a file - ignoring',
                        autopypath_path.resolve(strict=True),
                    )
                # load autopypath config for repo searching and update repo markers not set manually
                # This is done BEFORE checking for repo markers so that autopypath.toml
                # can redefine the repo markers used to identify the repo root if needed
                # without accidentally triggering on its own presence first (which could
                # happen because it is defined in the default markers so it can be used
                # to identify the repo root if wanted).
                else:
                    _log.debug('Loading autopypath.toml from: %s', autopypath_path)
                    self._autopypath = _AutopypathConfig(current_path)
                    if self.manual_config.repo_markers is None:
                        repo_markers = self.autopypath_config.repo_markers or repo_markers
                        _log.debug('Updated repo markers from autopypath.toml: %s', repo_markers)

            for marker, typ in repo_markers.items():
                test_path = current_path / marker
                if typ == _MarkerType.FILE and test_path.exists() and test_path.is_file():
                    _log.debug('Repository root found at: %s', current_path)
                    return current_path
                elif typ == _MarkerType.DIR and test_path.exists() and test_path.is_dir():
                    _log.debug('Repository root found at: %s', current_path)
                    return current_path
            if current_path == current_path.parent:
                break
            current_path = current_path.parent
        raise AutopypathError('Repository root could not be found.')

    def restore_sys_path(self) -> None:
        """Restores :data:`sys.path` to its original state before any modifications."""
        if not self.dry_run:
            sys.path = list(self.original_sys_path)
            _log.debug('sys.path restored to original state: %s', sys.path)
        else:
            _log.debug('Dry run - sys.path would be restored to original state: %s', self.original_sys_path)

    @property
    def load_strategy(self) -> _LoadStrategy:
        """The strategy for handling multiple :data:`sys.path` sources.

        :return LoadStrategy: The strategy for handling multiple :data:`sys.path` sources.
        """
        return self._load_strategy

    @property
    def paths(self) -> tuple[Path, ...]:
        """The final resolved paths that were added to :data:`sys.path`.

        :return tuple[Path, ...]: The final resolved paths.
        """
        return self._paths

    @property
    def path_resolution_order(self) -> tuple[_PathResolution, ...]:
        """The order in which to resolve :data:`sys.path` sources.

        :return tuple[PathResolution, ...]: The order in which to resolve :data:`sys.path` sources.
        """
        return self._path_resolution_order

    @property
    def repo_root_path(self) -> Path:
        """The repository root path based on the configured repo markers.

        :return Path: The repository root path.
        """
        return self._repo_root_path

    @property
    def context_file(self) -> Path:
        """The file path of the script that is configuring the Python path.

        This is the file that was used as the context for determining the repository root
        and configuring :data:`sys.path` accordingly. It is typically the script being executed.

        :return Path: The context file path.
        """
        return self._context_file

    @property
    def manual_config(self) -> _ManualConfig:
        """Manual configuration provided directly to the function.

        :return ManualConfig: The manual configuration.
        """
        return self._manual

    @property
    def autopypath_config(self) -> _AutopypathConfig:
        """Configuration loaded from autopypath.toml."""
        if self._autopypath is None:
            return _EMPTY_AUTOPYPATH_CONFIG  # Special empty config
        return self._autopypath

    @property
    def pyproject_config(self) -> _PyProjectConfig:
        """Configuration loaded from pyproject.toml.

        :return PyProjectConfig: The pyproject.toml configuration.
        """
        return self._pyproject

    @property
    def default_config(self) -> _DefaultConfig:
        """Default autopypath configuration.

        :return DefaultConfig: The default configuration.
        """
        return self._default

    @property
    def original_sys_path(self) -> tuple[str, ...]:
        """The original :data:`sys.path` before any modifications.

        :return tuple[str, ...]: The original :data:`sys.path`.
        """
        return tuple(self._original_sys_path)

    @property
    def updated_sys_path(self) -> tuple[str, ...]:
        """The updated :data:`sys.path` after modifications.

        :return tuple[str, ...]: The updated :data:`sys.path`.
        """
        return self._updated_paths

    @property
    def dry_run(self) -> bool:
        """Indicates whether the configuration was a dry run (no actual sys.path modification).

        :return bool: ``True`` if dry run, ``False`` otherwise.
        """
        return self._dry_run
