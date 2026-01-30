"""Tests for autopypath._config_py_path._config."""

import itertools
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Iterator, NamedTuple, Union

import pytest
from testspec import Assert, PytestAction, TestSpec

from autopypath._config_py_path._config import _Config
from autopypath._exceptions import AutopypathError
from autopypath._load_strategy import _LoadStrategy
from autopypath._marker_type import _MarkerType
from autopypath._path_resolution import _PathResolution
from autopypath._types import LoadStrategyLiterals, PathResolutionLiterals, RepoMarkerLiterals


class ConfigParameters(NamedTuple):
    """Combination of Config parameters for testing.

    :param MappingProxyType[str, MarkerType | RepoMarkerLiterals] | None repo_markers: Repository markers.
    :param tuple[str | Path, ...] | None paths: Additional paths.
    :param LoadStrategy | LoadStrategyLiterals | None load_strategy: Load strategy.
    :param tuple[PathResolution | PathResolutionLiterals, ...] | None path_resolution_order: Path resolution order.
    """

    repo_markers: Union[MappingProxyType[str, Union[_MarkerType, RepoMarkerLiterals]], None]
    paths: Union[tuple[str, ...], tuple[Path, ...], None]
    load_strategy: Union[_LoadStrategy, LoadStrategyLiterals, None]
    path_resolution_order: Union[tuple[Union[_PathResolution, PathResolutionLiterals], ...], None]


# fmt: off

@pytest.mark.parametrize(
    'testspec', [
        PytestAction('MARKER_001',
            name='Create Config with valid repo_markers',
            action=_Config,
            kwargs={'repo_markers': {'.git': _MarkerType.DIR, 'pyproject.toml': _MarkerType.FILE}},
            validate_attr='repo_markers',
            expected={'.git': _MarkerType.DIR, 'pyproject.toml': _MarkerType.FILE}),
        PytestAction('MARKER_002',
            name='Create Config with empty repo_markers',
            action=_Config, kwargs={'repo_markers': {}},
            validate_attr='repo_markers', expected=None),
        PytestAction('MARKER_003',
            name='Create Config with single repo_marker',
            action=_Config, kwargs={'repo_markers': {'setup.py': _MarkerType.FILE}},
            validate_attr='repo_markers', expected={'setup.py': _MarkerType.FILE}),
        PytestAction('MARKER_004',
            name='Create Config with string repo_markers',
            action=_Config, kwargs={'repo_markers': {'.git': 'dir', 'setup.py': 'file'}},
            validate_attr='repo_markers', expected={'.git': _MarkerType.DIR, 'setup.py': _MarkerType.FILE}),
        PytestAction('MARKER_005',
            name='Create Config with mixed type repo_markers',
            action=_Config, kwargs={'repo_markers': {'.git': _MarkerType.DIR, 'setup.py': 'file'}},
            validate_attr='repo_markers', expected={'.git': _MarkerType.DIR, 'setup.py': _MarkerType.FILE}),
        PytestAction('MARKER_006',
            name='Create Config with invalid repo_marker',
            action=_Config, kwargs={'repo_markers': {'.git': 'DIR'}},
            exception=AutopypathError),
        PytestAction('MARKER_007',
            name='Create Config with invalid repo_marker type',
            action=_Config, kwargs={'repo_markers': {'.git': 123}},
            exception=AutopypathError),
        PytestAction('MARKER_008',
            name='Create Config with None repo_markers',
            action=_Config, kwargs={'repo_markers': None},
            validate_attr='repo_markers', expected=None),
        PytestAction('MARKER_009',
            name='Create Config with no repo_markers',
            action=_Config, kwargs={},
            validate_attr='repo_markers', expected=None),
        PytestAction('MARKER_010',
            name='Create Config with whitespace repo_marker key',
            action=_Config, kwargs={'repo_markers': {'   ': _MarkerType.DIR}},
            exception=AutopypathError),
        PytestAction('MARKER_011',
            name='Create Config with non-string repo_marker key',
            action=_Config, kwargs={'repo_markers': {123: _MarkerType.DIR}},
            exception=AutopypathError),
        PytestAction('MARKER_012',
            name='Create Config with non-mapping repo_markers',
            action=_Config, kwargs={'repo_markers': [('setup.py', _MarkerType.FILE)]},
            exception=AutopypathError),
        PytestAction('MARKER_013',
            name='Create Config with repo_marker key exceeding max length',
            action=_Config, kwargs={'repo_markers': {'a' * 65: _MarkerType.DIR}},
            exception=AutopypathError),
        PytestAction('MARKER_014',
            name='Create Config with repo_marker key containing path separator',
            action=_Config, kwargs={'repo_markers': {'inva/lid': _MarkerType.DIR}},
            exception=AutopypathError),
        PytestAction('MARKER_015',
            name='Create Config with repo_marker key being Windows reserved name',
            action=_Config, kwargs={'repo_markers': {'CON': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_016',
            name='Create Config with repo_marker key containing forbidden characters',
            action=_Config, kwargs={'repo_markers': {'inva<lid': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_017',
            name='Create Config with repo_marker key being empty string',
            action=_Config, kwargs={'repo_markers': {'': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_018',
            name='Create Config with repo_marker key having leading whitespace',
            action=_Config, kwargs={'repo_markers': {'  setup.py': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_019',
            name='Create Config with repo_marker key having trailing whitespace',
            action=_Config, kwargs={'repo_markers': {'setup.py  ': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_020',
            name='Create Config with repo_marker key containing null character',
            action=_Config, kwargs={'repo_markers': {'setup\0.py': _MarkerType.FILE}},
            exception=AutopypathError),
        PytestAction('MARKER_021',
            name='Validate repo_marker attr returns MappingProxyType',
            action=_Config, kwargs={'repo_markers': {'setup.py': _MarkerType.FILE}},
            validate_attr='repo_markers', expected=MappingProxyType,
            assertion=Assert.ISINSTANCE),
    ]
)
def test_repo_markers(testspec: TestSpec) -> None:
    """Test Config with repo_markers."""
    testspec.run()

@pytest.mark.parametrize('testspec', [
    PytestAction('PATHS_001',
        name='Create Config with valid list of paths',
        action=_Config, kwargs={'paths': ['src', 'lib', 'utils']},
        validate_attr='paths', expected=(Path('src'), Path('lib'), Path('utils'))),
    PytestAction('PATHS_002',
        name='Create Config with empty paths',
        action=_Config, kwargs={'paths': []},
        validate_attr='paths', expected=None),
    PytestAction('PATHS_003',
        name='Create Config with single path',
        action=_Config, kwargs={'paths': ['src']},
        validate_attr='paths', expected=(Path('src'),)),
    PytestAction('PATHS_004',
        name='Create Config with None paths',
        action=_Config, kwargs={'paths': None},
        validate_attr='paths', expected=None),
    PytestAction('PATHS_005',
        name='Create Config with no paths',
        action=_Config, kwargs={},
        validate_attr='paths', expected=None),
    PytestAction('PATHS_006',
        name='Create Config with invalid path type',
        action=_Config, kwargs={'paths': ['src', 123, 'utils']},
        exception=AutopypathError),
    PytestAction('PATHS_007',
        name='Create Config with Path objects',
        action=_Config, kwargs={'paths': [Path('src'), Path('lib')]},
        validate_attr='paths', expected=(Path('src'), Path('lib'))),
    PytestAction('PATHS_008',
        name='Create Config with path having leading whitespace',
        action=_Config, kwargs={'paths': ['  src', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_009',
        name='Create Config with path having trailing whitespace',
        action=_Config, kwargs={'paths': ['src  ', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_010',
        name='Create Config with path being only whitespace',
        action=_Config, kwargs={'paths': ['   ', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_011',
        name='Create Config with path being only forward slashes',
        action=_Config, kwargs={'paths': ['///', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_012',
        name='Create Config with path being only backslashes',
        action=_Config, kwargs={'paths': ['\\\\\\', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_013',
        name='Create Config with path having segment with leading whitespace',
        action=_Config, kwargs={'paths': ['src/  utils', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_014',
        name='Create Config with path having segment with trailing whitespace',
        action=_Config, kwargs={'paths': ['src/utils  ', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_015',
        name='Create Config with path having whitespace segment',
        action=_Config, kwargs={'paths': ['src/ /utils', 'lib']},
        exception=AutopypathError),
    PytestAction('PATHS_016',
        name='Create Config with Path having segment being only whitespace',
        action=_Config, kwargs={'paths': [Path('src/   /utils'), Path('lib')]},
        exception=AutopypathError),
    PytestAction('PATHS_017',
        name='Create Config with Path having segment with leading whitespace',
        action=_Config, kwargs={'paths': [Path('src/  utils'), Path('lib')]},
        exception=AutopypathError),
    PytestAction('PATHS_018',
        name='Create Config with Path having segment with trailing whitespace',
        action=_Config, kwargs={'paths': [Path('src/utils  /more'), Path('lib')]},
        exception=AutopypathError),
    PytestAction('PATHS_019',
        name='Create config with path being empty string',
        action=_Config, kwargs={'paths': ['']},
        exception=AutopypathError),
    PytestAction('PATHS_020',
        name='Create config with path being neither str nor Path',
        action=_Config, kwargs={'paths': [123]},
        exception=AutopypathError),
    PytestAction('PATHS_021',
        name='Create config with paths being neither sequence nor None',
        action=_Config, kwargs={'paths': 123},
        exception=AutopypathError),
    PytestAction('PATHS_022',
        name='Validate paths attr returns tuple of Path objects',
        action=_Config, kwargs={'paths': ['src', 'lib']},
        validate_attr='paths', expected=tuple,
        assertion=Assert.ISINSTANCE),
])
def test_paths(testspec: TestSpec) -> None:
    """Test Config with paths"""
    testspec.run()


@pytest.mark.parametrize('testspec', [
    PytestAction('LOAD_001',
        name='Create Config with valid load_strategy',
        action=_Config,
        kwargs={'load_strategy': _LoadStrategy.PREPEND},
        validate_attr='load_strategy',
        expected=_LoadStrategy.PREPEND),
    PytestAction('LOAD_002',
        name='Create Config with load_strategy as string',
        action=_Config,
        kwargs={'load_strategy': 'prepend'},
        validate_attr='load_strategy',
        expected=_LoadStrategy.PREPEND),
    PytestAction('LOAD_003',
        name='Create Config with invalid load_strategy string',
        action=_Config,
        kwargs={'load_strategy': 'invalid_strategy'},
        exception=AutopypathError),
    PytestAction('LOAD_004',
        name='Create Config with invalid load_strategy type',
        action=_Config,
        kwargs={'load_strategy': 123},
        exception=AutopypathError),
    PytestAction('LOAD_005',
        name='Create Config with no load_strategy',
        action=_Config,
        kwargs={},
        validate_attr='load_strategy',
        expected=None),
    PytestAction('LOAD_006',
        name='Create Config with None load_strategy',
        action=_Config,
        kwargs={'load_strategy': None},
        validate_attr='load_strategy')
])
def test_load_strategy(testspec: TestSpec) -> None:
    """Test Config with load_strategy"""
    testspec.run()

@pytest.mark.parametrize('testspec', [
    PytestAction('RESOLVE_001',
        name='Create Config with valid path_resolution_order',
        action=_Config,
        kwargs={'path_resolution_order': [ 'manual', 'pyproject']},
        validate_attr='path_resolution_order',
        expected=(_PathResolution.MANUAL, _PathResolution.PYPROJECT)),
    PytestAction('RESOLVE_002',
        name='Create Config with path_resolution_order as enums',
        action=_Config,
        kwargs={'path_resolution_order': [_PathResolution.MANUAL]},
        validate_attr='path_resolution_order',
        expected=(_PathResolution.MANUAL,)),
    PytestAction('RESOLVE_003',
        name='Create Config with invalid path_resolution_order string',
        action=_Config,
        kwargs={'path_resolution_order': ['invalid_source']},
        exception=AutopypathError),
    PytestAction('RESOLVE_004',
        name='Create Config with invalid path_resolution_order type',
        action=_Config,
        kwargs={'path_resolution_order': [123]},
        exception=AutopypathError),
    PytestAction('RESOLVE_005',
        name='Create Config with empty path_resolution_order',
        action=_Config,
        kwargs={'path_resolution_order': []},
        validate_attr='path_resolution_order',
        expected=None),
    PytestAction('RESOLVE_006',
        name='Create Config with None path_resolution_order',
        action=_Config,
        kwargs={'path_resolution_order': None},
        validate_attr='path_resolution_order',
        expected=None),
    PytestAction('RESOLVE_007',
        name='Create Config with no path_resolution_order',
        action=_Config,
        kwargs={},
        validate_attr='path_resolution_order',
        expected=None),
    PytestAction('RESOLVE_008',
        name='Create Config with duplicate path_resolution_order entries',
        action=_Config,
        kwargs={'path_resolution_order': ['manual', 'pyproject', 'manual']},
        exception=AutopypathError),

    PytestAction('RESOLVE_010',
        name='Create Config with mixed type path_resolution_order entries',
        action=_Config,
        kwargs={'path_resolution_order': ['manual', _PathResolution.PYPROJECT]},
        validate_attr='path_resolution_order',
        expected=(_PathResolution.MANUAL, _PathResolution.PYPROJECT)),
    PytestAction('RESOLVE_011',
        name='Create Config with path_resolution_order having leading/trailing whitespace',
        action=_Config,
        kwargs={'path_resolution_order': [' manual ', 'pyproject']},
        exception=AutopypathError),
    PytestAction('RESOLVE_012',
        name='Create Config with path_resolution_order being neither sequence nor None',
        action=_Config,
        kwargs={'path_resolution_order': 123},
        exception=AutopypathError),
    PytestAction('RESOLVE_013',
        name='Create Config with path_resolution_order containing non-str/non-enum',
        action=_Config,
        kwargs={'path_resolution_order': ['manual', 123]},
        exception=AutopypathError),
    PytestAction('RESOLVE_014',
        name="Create config with path_resolution_order as a string",
        action=_Config,
        kwargs={'path_resolution_order': 'manual'},
        exception=AutopypathError),
])
def test_path_resolution_order(testspec: TestSpec) -> None:
    """Test Config with path_resolution_order"""
    testspec.run()


@pytest.mark.parametrize('testspec', [
    PytestAction('REPLACE_001',
        name='Use replace method to change repo_markers of Config',
        action=_Config().replace,
        kwargs={'repo_markers': {'.hg': _MarkerType.DIR}},
        validate_attr='repo_markers',
        expected={'.hg': _MarkerType.DIR}),
    PytestAction('REPLACE_002',
        name='Use replace method to change paths of Config',
        action=_Config().replace, kwargs={'paths': ['new_src', 'new_lib']},
        validate_attr='paths',
        expected=(Path('new_src'), Path('new_lib'))),
    PytestAction('REPLACE_003',
        name='Use replace method to change load_strategy of Config',
        action=_Config().replace, kwargs={'load_strategy': _LoadStrategy.REPLACE},
        validate_attr='load_strategy',
        expected=_LoadStrategy.REPLACE),
    PytestAction('REPLACE_004',
        name='Use replace method to change path_resolution_order of Config',
        action=_Config().replace, kwargs={'path_resolution_order': ['pyproject', 'manual']},
        validate_attr='path_resolution_order',
        expected=(_PathResolution.PYPROJECT, _PathResolution.MANUAL)),
    PytestAction('REPLACE_005',
        name='Use replace method with multiple changes to Config',
        action=_Config().replace,
        kwargs={
            'repo_markers': {'.svn': _MarkerType.DIR},
            'paths': ['another_src'],
            'load_strategy': 'prepend_highest_priority',
            'path_resolution_order': [_PathResolution.PYPROJECT]
        },
        validate_attr='repo_markers',
        expected={'.svn': _MarkerType.DIR}),
])
def test_replace(testspec: TestSpec) -> None:
    """Test Config replace method."""
    testspec.run()


@cache
def generate_all_config_combinations() -> tuple[tuple[_Config, ConfigParameters], ...]:
    """Generate all combinations of Config parameters for testing.

    Cached after first call to improve performance.

    Creates Config instances for every test combination of the following parameters:
    - repo_markers
    - paths
    - load_strategy
    - path_resolution_order

    :return tuple[tuple[Config, ConfigParameters], ...]: A tuple containing all generated Config instances and
        their corresponding parameter combinations.
    """
    repo_markers: tuple[Union[MappingProxyType[str, Union[_MarkerType, RepoMarkerLiterals]], None], ...] = (
        MappingProxyType({'.git': _MarkerType.DIR}),
        MappingProxyType({'pyproject.toml': _MarkerType.FILE}),
        MappingProxyType({'.git': _MarkerType.DIR, 'pyproject.toml': _MarkerType.FILE}),
        None,
    )

    paths: tuple[Union[tuple[str, ...], tuple[Path, ...], None], ...] = (
        ('src', 'lib'),
        ('utils',),
        None
    )

    load_strategies: tuple[Union[_LoadStrategy, LoadStrategyLiterals, None], ...] = (
        _LoadStrategy.PREPEND,
        _LoadStrategy.REPLACE,
        _LoadStrategy.PREPEND_HIGHEST_PRIORITY,
        None,
    )

    path_resolution_orders: tuple[Union[tuple[Union[_PathResolution, PathResolutionLiterals], ...], None], ...] = (
        (_PathResolution.MANUAL, _PathResolution.PYPROJECT),
        None,
    )

    # generate all combinations of the above parameters and creates tuples of
    # (Config instance, ConfigParameters) for each combination
    configs = []
    for rm, p, ls, pro in itertools.product(repo_markers, paths, load_strategies, path_resolution_orders):
        config = _Config(
                repo_markers=rm,
                paths=p,
                load_strategy=ls,
                path_resolution_order=pro)
        combination = ConfigParameters(rm, p, ls, pro)
        configs.append((config, combination))

    return tuple(configs)


# Efficiently generate only (i, j) pairs where i <= j to avoid redundant equality checks
# By making this a generator, we avoid storing all pairs in memory at once.
def config_combinations_pairs() -> Iterator[tuple[tuple[_Config, ConfigParameters], tuple[_Config, ConfigParameters]]]:
    configs: tuple[tuple[_Config, ConfigParameters], ...] = generate_all_config_combinations()
    n: int = len(configs)
    for i in range(n):
        for j in range(i, n):
            yield (configs[i], configs[j])


def test_eq() -> None:
    """Test Config equality comparison.

    Fails on first mismatch found.
    """
    n_combinations = len(generate_all_config_combinations())
    lower_limit_of_comparisons = n_combinations * (n_combinations + 1) // 2  # n * (n + 1) / 2
    counter = 0
    for config_a, config_b in config_combinations_pairs():
        assert (config_a[0] == config_b[0]) == (config_a[1] == config_b[1]), (
            f'EQ_001 Config equality failed for combinations: '
            f'Config A parameters: {config_a[1]} and '
            f'Config B parameters: {config_b[1]}'
        )
        counter += 1
    assert counter >= lower_limit_of_comparisons, (
        f"EQ_002 Test did not compare enough Config combinations: only {counter} comparisons made."
        f" Expected at least {lower_limit_of_comparisons}.")

    instance = _Config()
    result = instance == "not a config"
    assert not result, "EQ_003 Config __eq__ did not return False for a non-Config comparison."

def test_hash() -> None:
    """Test Config hashing.

    Fails on first mismatch found.
    """
    n_combinations = len(generate_all_config_combinations())
    lower_limit_of_comparisons = n_combinations * (n_combinations + 1) // 2  # n * (n + 1) / 2
    counter = 0
    for config_a, config_b in config_combinations_pairs():
        assert (hash(config_a[0]) == hash(config_b[0])) == (config_a[1] == config_b[1]), (
            f'HASH_001 Config hash comparison failed for combinations: '
            f'Config A parameters: {config_a[1]} and '
            f'Config B parameters: {config_b[1]}'
        )
        counter += 1
    assert counter >= lower_limit_of_comparisons, (
        f"HASH_002 Test did not compare enough Config combinations: only {counter} comparisons made."
        f" Expected at least {lower_limit_of_comparisons}.")


def test_repr() -> None:
    """Test Config __repr__ method."""
    # Note - use of eval on the repr output to reconstitute the Config instance
    # and compare to the original. This is safe in this controlled test context
    # where we know the input values and expected output. In general, eval
    # should be avoided due to security risks. IOW: This is a test-only use of eval.
    config = _Config(
        repo_markers={'.git': 'dir'},
        paths=['src', 'lib'],
        load_strategy='prepend',
        path_resolution_order=['manual', 'pyproject']
    )

    reconstituted_config = eval(repr(config))
    assert reconstituted_config == config, (
        "REPR_001 Reconstituted Config from __repr__ does not match original. "
        f'Original: {config!r}, Reconstituted: {reconstituted_config!r}'
    )

    config = _Config()
    reconstituted_config = eval(repr(config))
    assert reconstituted_config == config, (
        "REPR_002 Reconstituted default Config from __repr__ does not match original. "
        f'Original: {config!r}, Reconstituted: {reconstituted_config!r}'
    )

    config = _Config(
        repo_markers=None,
        paths=None,
        load_strategy=None,
        path_resolution_order=None
    )
    reconstituted_config = eval(repr(config))
    assert reconstituted_config == config, (
        "REPR_003 Reconstituted all-None Config from __repr__ does not match original. "
        f'Original: {config!r}, Reconstituted: {reconstituted_config!r}'
    )


def test_str() -> None:
    """Test Config __str__ method."""
    config = _Config(
        repo_markers={'.git': 'dir'},
        paths=['src', 'lib'],
        load_strategy='prepend',
        path_resolution_order=['manual', 'pyproject']
    )
    expected_str = repr(config)
    assert str(config) == expected_str, "STR_001 Config __str__ output mismatch."

# fmt: on
