"""Tests for :mod:`autopypath._config_py_path._config_py_path`."""

import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from autopypath import AutopypathError
from autopypath import _defaults as defaults
from autopypath._config_py_path._config_py_path import _EMPTY_AUTOPYPATH_CONFIG, _NON_RESOLVABLE_SYS_PATH, _ConfigPyPath
from autopypath._types import _NoPath

_ORIGINAL_SYS_PATH: list[str] = sys.path.copy()
_ORIGINAL_NAME: str = __name__


def setup_function() -> None:
    """Setup function to reset sys.path before each test."""
    sys.path = _ORIGINAL_SYS_PATH.copy()


def teardown_function() -> None:
    """Teardown function to reset sys.path after each test."""
    sys.path = _ORIGINAL_SYS_PATH.copy()


def test_empty_autopypath_config() -> None:
    """Tests the special empty AutopypathConfig instance."""
    assert isinstance(_EMPTY_AUTOPYPATH_CONFIG.toml_filepath, _NoPath), (
        'EMPTY_AUTO_001 _EMPTY_AUTOPYPATH_CONFIG.toml_filepath should be a _NoPath instance'
    )
    assert _EMPTY_AUTOPYPATH_CONFIG.repo_markers is None, (
        'EMPTY_AUTO_002 _EMPTY_AUTOPYPATH_CONFIG.repo_markers should be None'
    )
    assert _EMPTY_AUTOPYPATH_CONFIG.paths is None, 'EMPTY_AUTO_003 _EMPTY_AUTOPYPATH_CONFIG.paths should be None'
    assert _EMPTY_AUTOPYPATH_CONFIG.load_strategy is None, (
        'EMPTY_AUTO_004 _EMPTY_AUTOPYPATH_CONFIG.load_strategy should be None'
    )
    assert _EMPTY_AUTOPYPATH_CONFIG.path_resolution_order is None, (
        'EMPTY_AUTO_005 _EMPTY_AUTOPYPATH_CONFIG.path_resolution_order should be None'
    )


def test_configured_autopypath_config(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.autopypath_config returns the correct configuration
    when an autopypath.toml file exists in the root of the repository.

    We want to test various combinations of existing and non-existing paths
    specified in the autopypath.toml file.

    'src' exists, 'tests' does not exist.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    src_path = root_path / 'src'
    src_path.mkdir()
    git_path = root_path / '.git'
    git_path.mkdir()
    autopypath_path = root_path / 'autopypath.toml'
    # Note: only "src" exists, "tests" does not exist
    autopypath_path.write_text("""
[tool.autopypath]
load_strategy = "replace"
path_resolution_order = ["manual", "autopypath", "pyproject"]
repo_markers = {".git" = "dir", "setup.py" = "file"}
paths=["src", "tests"]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )
    autopypath_config = config.autopypath_config
    assert autopypath_config.load_strategy == 'replace', (
        'AUTOPYPATH_CONFIGURED_001 autopypath_config.load_strategy should be LoadStrategy.REPLACE'
    )
    assert autopypath_config.path_resolution_order == (
        'manual',
        'autopypath',
        'pyproject',
    ), (
        'AUTOPYPATH_CONFIGURED_002 autopypath_config.path_resolution_order should match the configured '
        ' path resolution order: ["manual", "autopypath", "pyproject"]'
    )
    assert autopypath_config.repo_markers == {'.git': 'dir', 'setup.py': 'file'}, (
        'AUTOPYPATH_CONFIGURED_003 autopypath_config.repo_markers should match the configured repo markers'
    )
    if isinstance(autopypath_config.paths, Sequence):
        assert len(autopypath_config.paths) == 2, (
            'AUTOPYPATH_CONFIGURED_004 autopypath_config.paths should '
            'have length 2 because src and tests were configured'
        )
        assert str(autopypath_config.paths[0].name) == 'src', (
            'AUTOPYPATH_CONFIGURED_005 autopypath_config.paths should match the configured paths'
        )
        assert autopypath_config.paths[0].is_dir(), (
            'AUTOPYPATH_CONFIGURED_006 autopypath_config.paths[0] should be match the path to src directory'
        )
        assert src_path.resolve() == autopypath_config.paths[0].resolve(), (
            'AUTOPYPATH_CONFIGURED_007 autopypath_config.paths[0] should resolve to the src directory path'
        )
    else:
        pytest.fail('AUTOPYPATH_CONFIGURED_008 autopypath_config.paths should be a list')


def test_default_config(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.autopypath_config returns the special empty config when appropriate.
    Uses a temporary directory to simulate a repository without any autopypath configuration
    and a pyproject.toml file to mark the root.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.some_other_tool]
""")

    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )

    default_config = config.default_config
    assert default_config.load_strategy == defaults._LOAD_STRATEGY, (
        'DEFAULT_CONFIG_001 default_config.load_strategy should match defaults._LOAD_STRATEGY'
    )
    assert default_config.path_resolution_order == defaults._PATH_RESOLUTION_ORDER, (
        'DEFAULT_CONFIG_002 default_config.path_resolution_order should match defaults._PATH_RESOLUTION_ORDER'
    )
    assert default_config.repo_markers == defaults._REPO_MARKERS, (
        'DEFAULT_CONFIG_003 default_config.repo_markers should match defaults._REPO_MARKERS'
    )
    assert default_config.paths == defaults._PATHS


def test_no_pyproject_toml_file(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.pyproject_config returns an empty config when
    no pyproject.toml configuration file exists

    Uses a temporary directory to simulate a repository with an empty autopypath config in pyproject.toml.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()

    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )

    pyproject_config = config.pyproject_config
    assert pyproject_config.load_strategy is None, 'NO_PYPROJECT_FILE_001 pyproject_config.load_strategy should be None'
    assert pyproject_config.path_resolution_order is None, (
        'NO_PYPROJECT_FILE_002 pyproject_config.path_resolution_order should be None'
    )
    assert pyproject_config.repo_markers is None, 'NO_PYPROJECT_FILE_003 pyproject_config.repo_markers should be None'
    assert pyproject_config.paths is None, 'NO_PYPROJECT_FILE_004 pyproject_config.paths should be None'


def test_empty_pyproject_config(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.pyproject_config returns an empty config when pyproject.toml
    exists but has no autopypath configuration.

    Uses a temporary directory to simulate a repository with an empty autopypath config in pyproject.toml.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.some_other_tool]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )

    pyproject_config = config.pyproject_config
    assert pyproject_config.load_strategy is None, (
        'EMPTY_PYPROJECT_CONFIG_001 pyproject_config.load_strategy should be None'
    )
    assert pyproject_config.path_resolution_order is None, (
        'EMPTY_PYPROJECT_CONFIG_002 pyproject_config.path_resolution_order should be None'
    )
    assert pyproject_config.repo_markers is None, (
        'EMPTY_PYPROJECT_CONFIG_003 pyproject_config.repo_markers should be None'
    )
    assert pyproject_config.paths is None, 'EMPTY_PYPROJECT_CONFIG_004 pyproject_config.paths should be None'


def test_configured_pyproject_config(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.pyproject_config returns the correct configuration
    when a pyproject.toml file exists in the root of the repository.

    We want to test various combinations of existing and non-existing paths
    specified in the autopypath.toml file.

    'src' exists, 'tests' does not exist.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    src_path = root_path / 'src'
    src_path.mkdir()
    git_path = root_path / '.git'
    git_path.mkdir()
    pyproject_path = root_path / 'pyproject.toml'
    # Note: only "src" exists, "tests" does not exist
    pyproject_path.write_text("""
[tool.autopypath]
load_strategy = "prepend_highest_priority"
path_resolution_order = ["manual", "autopypath", "pyproject"]
repo_markers = {".git" = "dir", "setup.py" = "file"}
paths=["src", "tests"]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )
    pyproject_config = config.pyproject_config
    assert pyproject_config.load_strategy == 'prepend_highest_priority', (
        'PYPROJECT_CONFIGURED_001 pyproject_config.load_strategy should be LoadStrategy.PREPEND_HIGHEST_PRIORITY'
    )
    assert pyproject_config.path_resolution_order == (
        'manual',
        'autopypath',
        'pyproject',
    ), (
        'PYPROJECT_CONFIGURED_002 pyproject_config.path_resolution_order should match the configured '
        ' path resolution order: ["manual", "autopypath", "pyproject"]'
    )
    assert pyproject_config.repo_markers == {'.git': 'dir', 'setup.py': 'file'}, (
        'PYPROJECT_CONFIGURED_003 pyproject_config.repo_markers should match the configured repo markers'
    )
    if isinstance(pyproject_config.paths, Sequence):
        assert len(pyproject_config.paths) == 2, (
            'PYPROJECT_CONFIGURED_004 pyproject_config.paths should have length 2 because src and tests were configured'
        )
        assert str(pyproject_config.paths[0].name) == 'src', (
            'PYPROJECT_CONFIGURED_005 pyproject_config.paths should match the configured paths'
        )
        assert str(pyproject_config.paths[1].name) == 'tests', (
            'PYPROJECT_CONFIGURED_006 pyproject_config.paths should match the configured paths'
        )
        assert pyproject_config.paths[0].is_dir(), (
            'PYPROJECT_CONFIGURED_007 pyproject_config.paths[0] should be match the path to src directory'
        )
        assert src_path.resolve() == pyproject_config.paths[0].resolve(), (
            'PYPROJECT_CONFIGURED_008 pyproject_config.paths[0] should resolve to the src directory path'
        )
    else:
        pytest.fail('PYPROJECT_CONFIGURED_009 pyproject_config.paths should be a list')


def test_no_autopypath_toml_file(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.autopypath_config returns the special empty config when
    no autopypath.toml configuration file exists

    Uses a temporary directory to simulate a repository with an empty autopypath config in pyproject.toml.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.some_other_tool]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
    )

    autopypath_config = config.autopypath_config
    assert autopypath_config.load_strategy is None, (
        'NO_AUTOPYPATH_FILE_001 autopypath_config.load_strategy should be None'
    )
    assert autopypath_config.path_resolution_order is None, (
        'NO_AUTOPYPATH_FILE_002 autopypath_config.path_resolution_order should be None'
    )
    assert autopypath_config.repo_markers is None, (
        'NO_AUTOPYPATH_FILE_003 autopypath_config.repo_markers should be None'
    )
    assert autopypath_config.paths is None, 'NO_AUTOPYPATH_FILE_004 autopypath_config.paths should be None'


def test_manual_config(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath.manual_config returns an empty config when no manual
    configuration is provided.

    Uses a temporary directory to simulate a repository without any manual configuration.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    hg_path = root_path / '.hg'
    hg_path.mkdir()

    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
        load_strategy='prepend',
        path_resolution_order=['manual', 'autopypath'],
        paths=['src', 'tests'],
        repo_markers={'.hg': 'dir'},
    )

    manual_config = config.manual_config
    assert manual_config.load_strategy, 'MANUAL_CONFIG_001 manual_config.load_strategy should not be None'
    assert manual_config.path_resolution_order, (
        'MANUAL_CONFIG_002 manual_config.path_resolution_order should not be None'
    )
    assert isinstance(manual_config.paths, Sequence), 'MANUAL_CONFIG_003 manual_config.paths should be a Sequence'
    assert manual_config.repo_markers == {'.hg': 'dir'}, (
        'MANUAL_CONFIG_004 manual_config.repo_markers should match the provided manual configuration'
    )

    if isinstance(manual_config.paths, Sequence):
        assert len(manual_config.paths) == 2, (
            'MANUAL_CONFIG_005 manual_config.paths should have length 2 because src and tests were provided'
        )
        assert str(manual_config.paths[0].name) == 'src', (
            'MANUAL_CONFIG_006 manual_config.paths should match the provided manual configuration paths'
        )
        assert str(manual_config.paths[1].name) == 'tests', (
            'MANUAL_CONFIG_007 manual_config.paths should match the provided manual configuration paths'
        )
    else:
        pytest.fail('MANUAL_CONFIG_008 manual_config.paths should be a list')


def test_replace_strategy_live(tmp_path: Path) -> None:
    """
    Performs live tests of the 'replace' load strategy.

    Default sys.path is preserved and restored after the test.

    :param Path tmp_path: Path to a temporary directory for testing.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    vcs_path = root_path / '.vcs'
    vcs_path.mkdir()

    # src and tests do not exist - expect RuntimeError
    sys_path_before: list[str] = sys.path.copy()
    try:
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='replace',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )
        pytest.fail('REPLACE_STRATEGY_LIVE_001 Expected AutopypathError because no paths exist to replace sys.path')

    except AutopypathError:
        pass  # Expected because paths do not exist at all
    finally:
        sys.path = sys_path_before

    # Create the 'src' directory so one of the paths exists
    try:
        src_path = root_path / 'src'
        src_path.mkdir()

        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='replace',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )

        assert len(sys.path) == 1, (
            'REPLACE_STRATEGY_LIVE_002 sys.path should have length 1 after replace strategy is applied'
        )
        assert sys.path[0] == str(src_path.resolve()), (
            'REPLACE_STRATEGY_LIVE_003 sys.path[0] should be the src directory path'
        )
    finally:
        sys.path = sys_path_before


def test_prepend_strategy_live(tmp_path: Path) -> None:
    """
    Performs live tests of the 'prepend' load strategy.

    Default sys.path is preserved and restored after the test.

    :param Path tmp_path: Path to a temporary directory for testing.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    vcs_path = root_path / '.vcs'
    vcs_path.mkdir()

    # src and tests do not exist - expect no changes to sys.path
    sys_path_before: list[str] = sys.path.copy()
    try:
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='prepend',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )

        assert sys.path == sys_path_before, (
            'PREPEND_STRATEGY_LIVE_001 sys.path should be unchanged because no valid paths exist to prepend'
        )
    finally:
        sys.path = sys_path_before

    # Create the 'src' directory so one of the paths exists
    try:
        src_path = root_path / 'src'
        src_path.mkdir()

        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='prepend',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )

        assert len(sys.path) == len(sys_path_before) + 1, (
            'PREPEND_STRATEGY_LIVE_002 sys.path should have one additional entry after prepend strategy is applied'
        )
        assert sys.path[0] == str(src_path.resolve()), (
            'PREPEND_STRATEGY_LIVE_003 sys.path[0] should be the src directory path'
        )
        assert sys.path[1:] == sys_path_before, (
            'PREPEND_STRATEGY_LIVE_004 sys.path entries after the first should be unchanged'
        )
    finally:
        sys.path = sys_path_before


def test_prepend_highest_priority_strategy_live(tmp_path: Path) -> None:
    """
    Performs live tests of the 'prepend_highest_priority' load strategy.

    Default sys.path is preserved and restored after the test.

    :param Path tmp_path: Path to a temporary directory for testing.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    vcs_path = root_path / '.vcs'
    vcs_path.mkdir()

    # src and tests do not exist - expect no changes to sys.path
    sys_path_before: list[str] = sys.path.copy()
    try:
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='prepend_highest_priority',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )

        assert sys.path == sys_path_before, (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_001 sys.path should be '
            'unchanged because no valid paths exist to prepend'
        )
    finally:
        sys.path = sys_path_before

    assert sys.path == sys_path_before, (
        'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_002 sys.path should be have been restored to its original state'
    )
    # Create the 'src' directory so one of the paths exists
    try:
        src_path = root_path / 'src'
        src_path.mkdir()

        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='prepend_highest_priority',
            path_resolution_order=['manual'],
            paths=['src', 'tests'],
            repo_markers={'.vcs': 'dir'},
        )

        assert len(sys.path) == len(sys_path_before) + 1, (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_003 sys.path should have '
            'one additional entry after prepend_highest_priority strategy is applied'
            f': {sys.path}'
        )
        assert sys.path[0] == str(src_path.resolve()), (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_004 sys.path[0] should be the src directory path'
        )
        assert sys.path[1:] == sys_path_before, (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_005 sys.path entries after the first should be unchanged'
        )
    finally:
        sys.path = sys_path_before

    assert sys.path == sys_path_before, (
        'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_006 sys.path should be have been restored to its original state'
    )

    # Now create a autopypath.toml file that specifies a lower precedence paths
    # setting of ['tests'] rather than ['src', 'tests'] from the manual config
    # and create the 'tests' directory so that path exists
    try:
        autopypath_path = root_path / 'autopypath.toml'
        autopypath_path.write_text("""
[tool.autopypath]
load_strategy = "prepend_highest_priority"
path_resolution_order = ["autopypath", "manual"]
repo_markers = {".vcs" = "dir"}
paths=["tests"]
""")
        tests_path = root_path / 'tests'
        tests_path.mkdir()

        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            load_strategy='prepend_highest_priority',
            path_resolution_order=['manual', 'autopypath'],
            paths=['src'],
            repo_markers={'.vcs': 'dir'},
        )
        # autopypath and manual configs both have valid paths, but manual has
        # the higher priority so only 'src' should be added to sys.path
        assert len(sys.path) == len(sys_path_before) + 1, (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_007 sys.path should have one'
            'additional entry after prepend_highest_priority strategy is applied '
            'with autopypath.toml '
        )
        assert sys.path[0] == str(src_path.resolve()), (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_008 sys.path[0] should be the src directory path'
        )
        assert sys.path[1:] == sys_path_before, (
            'PREPEND_HIGHEST_PRIORITY_STRATEGY_LIVE_009 sys.path entries after the first should be unchanged'
        )
    finally:
        sys.path = sys_path_before


def test_strict(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Tests that _ConfigPyPath raises AutopypathError in strict mode
    when no valid paths are found to add to sys.path for non-replace
    load strategies.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    autopypath_path = root_path / 'autopypath.toml'
    # Note: both "src" and "tests" do not exist
    autopypath_path.write_text("""
[tool.autopypath]
load_strategy = "prepend"
path_resolution_order = ["manual", "autopypath", "pyproject"]
repo_markers = {".git" = "dir"}
paths=["src", "tests"]
""")
    try:
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            dry_run=True,
            strict=True,
        )
        pytest.fail('STRICT_001 Expected AutopypathError because no paths exist and strict mode is enabled')
    except AutopypathError:
        pass  # Expected because paths do not exist

    # Now test that a warning is logged for non-strict mode
    caplog.clear()
    _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
        strict=False,
    )
    warning_messages = [record.message for record in caplog.records if record.levelno == logging.WARNING]
    assert any(
        'autopypath: No valid paths to add to sys.path after processing.' in message for message in warning_messages
    ), 'STRICT_002 Expected a warning about no valid paths to add to sys.path in non-strict mode'


def test_symlinked_paths(tmp_path: Path) -> None:
    """Test Config with symlinked paths."""
    if os.name == 'nt':
        pytest.skip('SYMLINKED_PATHS tests are skipped on Windows due to symlink permission issues.')
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
paths = ["symlinked_path"]
""")
    symlink_target = root_path / 'actual_path'
    symlink_target.mkdir()
    symlink_path = root_path / 'symlinked_path'
    symlink_path.symlink_to(symlink_target, target_is_directory=True)

    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
        )
        new_path_entry = str((root_path / 'symlinked_path').resolve())
        assert new_path_entry in sys.path, 'SYMLINKED_PATHS_001 The resolved symlinked path should be in sys.path'
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()

    # remove the target directory and test that the symlink is ignored
    symlink_target.rmdir()
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
        )
        new_path_entry = str((root_path / 'symlinked_path').resolve())
        assert new_path_entry not in sys.path, (
            'SYMLINKED_PATHS_002 The symlinked path should be ignored since the target does not exist'
        )
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()


def test_non_resolvable_sys_path_entry(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that non-resolvable sys.path entries are handled gracefully."""

    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    src_path = root_path / 'src'
    src_path.mkdir()

    bogus_path = '::nota\0path::'
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy() + [bogus_path]
        caplog.clear()
        _ConfigPyPath(
            context_file=root_path / 'some_file.txt',
            log_level=logging.DEBUG,
        )
        messages = [record.message for record in caplog.records]
        if not any(message.startswith(_NON_RESOLVABLE_SYS_PATH) for message in messages):
            pytest.fail('NON_RESOLVABLE_SYS_PATH_001 Expected a log message about the non-resolvable sys.path entry')

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()


def test_non_file_autopypath_toml(tmp_path: Path) -> None:
    """Test that a non-file autopypath.toml is handled gracefully."""

    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    autopypath_path = root_path / 'autopypath.toml'
    autopypath_path.mkdir()  # Create a directory instead of a file

    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        config = _ConfigPyPath(
            context_file=context_file,
        )
        autopypath_config = config.autopypath_config
        assert autopypath_config == _EMPTY_AUTOPYPATH_CONFIG, (
            'NON_FILE_AUTOPYPATH_TOML_001 autopypath_config should '
            'be the empty config when autopypath.toml is not a file'
        )
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()

    # Now with strict
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        _ConfigPyPath(
            context_file=context_file,
            strict=True,
        )
        pytest.fail(
            'NON_FILE_AUTOPYPATH_TOML_002 Expected AutopypathError because autopypath.toml is not a file in strict mode'
        )
    except AutopypathError:
        pass
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()


def test_no_repo(tmp_path: Path) -> None:
    """Test that a AutopypathError is raised when no repository markers are found."""
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')

    try:
        _ConfigPyPath(
            context_file=context_file,
            dry_run=True,
            repo_markers={'.nonexistent_vcs': 'dir'},
        )
        pytest.fail('NO_REPO_001 Expected AutopypathError because no repository markers were found')
    except AutopypathError:
        pass  # Expected because no repository markers exist


def test_restore_sys_path(tmp_path: Path) -> None:
    """Test that sys.path is restored on call to _config.restore_sys_path()."""
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    src_path = root_path / 'src'
    src_path.mkdir()

    # dry run - sys.path should not be modified
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        config = _ConfigPyPath(
            context_file=context_file,
            load_strategy='prepend',
            path_resolution_order=['manual'],
            paths=['src'],
            repo_markers={'.git': 'dir'},
            dry_run=True,
        )

        assert sys.path == _ORIGINAL_SYS_PATH, 'RESTORE_SYS_PATH_001 sys.path should be unchanged in dry run mode'
        config.restore_sys_path()
        assert sys.path == _ORIGINAL_SYS_PATH, (
            'RESTORE_SYS_PATH_002 sys.path should be still be unchanged after restore_sys_path() is called'
        )

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()

    # live - sys.path should be modified and then restored
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        config = _ConfigPyPath(
            context_file=context_file,
            load_strategy='prepend',
            path_resolution_order=['manual'],
            paths=['src'],
            repo_markers={'.git': 'dir'},
        )

        assert len(sys.path) == len(_ORIGINAL_SYS_PATH) + 1, (
            'RESTORE_SYS_PATH_001 sys.path should have one additional entry after prepend strategy is applied'
        )
        config.restore_sys_path()
        assert sys.path == _ORIGINAL_SYS_PATH, (
            'RESTORE_SYS_PATH_002 sys.path should be restored to its original state after restore_sys_path() is called'
        )

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()


def test_updated_sys_path_property(tmp_path: Path) -> None:
    """Test that _ConfigPyPath.updated_sys_path property is unchanged in dry run mode.
    It should return the expected sys.path
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    context_file = root_path / 'some_file.txt'
    context_file.write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    src_path = root_path / 'src'
    src_path.mkdir()

    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        config = _ConfigPyPath(
            context_file=context_file,
            load_strategy='prepend',
            path_resolution_order=['manual'],
            paths=['src'],
            repo_markers={'.git': 'dir'},
            dry_run=True,
        )

        updated_sys_path = config.updated_sys_path
        assert len(updated_sys_path) == len(_ORIGINAL_SYS_PATH), (
            'UPDATED_SYS_PATH_001 updated_sys_path should have one additional entry after prepend strategy is applied'
        )

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()


def test_path_order_resolution(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath correctly resolves configuration
    for path resolution order specified in various configuration sources.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()

    manual_src_path = root_path / 'manual_src'
    manual_src_path.mkdir()

    pyproject_src_path = root_path / 'pyproject_src'
    pyproject_src_path.mkdir()

    autopypath_src_path = root_path / 'autopypath_src'
    autopypath_src_path.mkdir()

    # Create pyproject.toml with some configuration
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
load_strategy = "prepend"
path_resolution_order = ["pyproject"]
repo_markers = {".git" = "dir"}
paths=["pyproject_src"]
""")

    # Create autopypath.toml with some configuration
    autopypath_path = root_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
load_strategy = "prepend"
path_resolution_order = ["autopypath", "pyproject"]
repo_markers = {".git" = "dir"}
paths=["autopypath_src"]
""")

    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        load_strategy='prepend',
        path_resolution_order=['manual', 'autopypath', 'pyproject'],
        paths=['manual_src'],
        repo_markers={'.git': 'dir'},
    )

    # manual config should be highest precedence and thus first in sys.path
    assert sys.path[0] == str(manual_src_path), (
        f'PATH_ORDER_RESOLUTION_001 manual_src should be first in updated_sys_path: {sys.path!r}'
    )

    # autopypath.toml config should be second precedence
    assert sys.path[1] == str(autopypath_src_path), (
        f'PATH_ORDER_RESOLUTION_002 autopypath_src should be second in updated_sys_path: {sys.path!r}'
    )

    # pyproject.toml config should be third precedence
    assert sys.path[2] == str(pyproject_src_path), (
        f'PATH_ORDER_RESOLUTION_003 pyproject_src should be third in updated_sys_path: {sys.path!r}'
    )

    config.restore_sys_path()

    # reverse the order to verify it wasn't a fluke
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        load_strategy='prepend',
        path_resolution_order=['pyproject', 'autopypath', 'manual'],
        paths=['manual_src'],
        repo_markers={'.git': 'dir'},
    )

    # pyproject.toml config should be first precedence
    assert sys.path[0] == str(pyproject_src_path), (
        f'PATH_ORDER_RESOLUTION_006 pyproject_src should be first in updated_sys_path: {sys.path!r}'
    )
    # autopypath.toml config should be third precedence
    assert sys.path[1] == str(autopypath_src_path), (
        f'PATH_ORDER_RESOLUTION_007 autopypath_src should be second in updated_sys_path: {sys.path!r}'
    )
    # manual config should be fourth precedence
    assert sys.path[2] == str(manual_src_path), (
        f'PATH_ORDER_RESOLUTION_008 manual_src should be third in updated_sys_path: {sys.path!r}'
    )

    sys.path = []  # Clear sys.path for next test

    # Finally, test with only autopypath.toml and pyproject.toml configs
    # manual is not in the resolution order
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        load_strategy='prepend',
        path_resolution_order=['autopypath', 'pyproject'],
        repo_markers={'.git': 'dir'},
    )
    # autopypath.toml config should be first precedence
    assert sys.path[0] == str(autopypath_src_path), (
        f'PATH_ORDER_RESOLUTION_009 autopypath_src should be first in updated_sys_path: {sys.path!r}'
    )
    # pyproject.toml config should be second precedence
    assert sys.path[1] == str(pyproject_src_path), (
        f'PATH_ORDER_RESOLUTION_010 pyproject_src should be second in updated_sys_path: {sys.path!r}'
    )

    assert len(sys.path) == 2, f'PATH_ORDER_RESOLUTION_011 updated_sys_path should have length 2: {sys.path!r}'

    sys.path = _ORIGINAL_SYS_PATH.copy()


def test_load_strategy_precedence(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath respects the load_strategy precedence
    in the hierarchical configuration resolution.

    manual > autopypath.toml > pyproject.toml  > defaults.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    src_path = root_path / 'src'
    src_path.mkdir()

    # Create pyproject.toml with load_strategy configuration
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
load_strategy = "replace"
path_resolution_order = ["pyproject"]
repo_markers = {".git" = "dir"}
paths=["src"]
""")
    # Create autopypath.toml with load_strategy configuration
    autopypath_path = root_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
load_strategy = "prepend"
path_resolution_order = ["autopypath", "pyproject"]
repo_markers = {".git" = "dir"}
paths=["src"]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        load_strategy='prepend_highest_priority',
        path_resolution_order=['manual', 'autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )

    # manual config should be highest precedence and hence the winner
    assert config.load_strategy == 'prepend_highest_priority', (
        'LOAD_STRATEGY_PRECEDENCE_001 load_strategy should be prepend_highest_priority from manual config'
    )

    # autopypath.toml config should winner as second precedence without a manual load_strategy
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.load_strategy == 'prepend', (
        'LOAD_STRATEGY_PRECEDENCE_002 load_strategy should be prepend from autopypath.toml config'
    )

    # pyproject.toml config should be winner as third precedence without manual or autopypath load_strategy
    autopypath_path.unlink()  # Remove autopypath.toml to test pyproject.toml precedence

    # Create autopypath.toml without load_strategy configuration
    autopypath_path = root_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
path_resolution_order = ["autopypath", "pyproject"]
repo_markers = {".git" = "dir"}
paths=["src"]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.load_strategy == 'replace', (
        'LOAD_STRATEGY_PRECEDENCE_003 load_strategy should be replace from pyproject.toml config'
    )

    # finally, defaults should be winner without any load_strategy configured

    autopypath_path.unlink()  # Remove autopypath.toml to test default precedence
    pyproject_path.unlink()  # Remove pyproject.toml to test default precedence

    # default load_strategy should be winner without manual, autopypath, or pyproject load_strategy
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.load_strategy == defaults._LOAD_STRATEGY, (
        'LOAD_STRATEGY_PRECEDENCE_004 load_strategy should be prepend from default configuration'
    )


def test_path_resolution_order_precedence(tmp_path: Path) -> None:
    """Tests that _ConfigPyPath respects the path_resolution_order precedence
    in the hierarchical configuration resolution.

    manual > autopypath.toml > pyproject.toml  > defaults.

    Uses a temporary directory to simulate a repository with an autopypath.toml file.
    """
    root_path = tmp_path / 'repo'
    root_path.mkdir()
    root_path.joinpath('some_file.txt').write_text('Just a test file.')
    git_path = root_path / '.git'
    git_path.mkdir()
    src_path = root_path / 'src'
    src_path.mkdir()

    # Create pyproject.toml with path_resolution_order configuration
    pyproject_path = root_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
path_resolution_order = ["pyproject"]
repo_markers = {".git" = "dir"}
paths=["src"]
""")
    # Create autopypath.toml with path_resolution_order configuration
    autopypath_path = root_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
path_resolution_order = ["autopypath", "pyproject"]
repo_markers = {".git" = "dir"}
paths=["src"]
""")
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['manual', 'autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    # manual config should be highest precedence and hence the winner
    assert config.path_resolution_order == ('manual', 'autopypath', 'pyproject'), (
        'PATH_RESOLUTION_ORDER_PRECEDENCE_001 path_resolution_order should be '
        f'["manual", "autopypath", "pyproject"] from manual config: {config.path_resolution_order}'
    )
    # autopypath.toml config should winner as second precedence without a manual path_resolution_order
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['autopypath', 'pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.path_resolution_order == ('autopypath', 'pyproject'), (
        'PATH_RESOLUTION_ORDER_PRECEDENCE_002 path_resolution_order should be '
        '["autopypath", "pyproject"] from autopypath.toml config'
    )
    # pyproject.toml config should be winner as third precedence without manual or autopypath path_resolution_order
    autopypath_path.unlink()  # Remove autopypath.toml to test pyproject.toml precedence
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        path_resolution_order=['pyproject'],
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.path_resolution_order == ('pyproject',), (
        'PATH_RESOLUTION_ORDER_PRECEDENCE_003 path_resolution_order should be ["pyproject"] from pyproject.toml config'
    )
    # finally, defaults should be winner without any path_resolution_order configured
    pyproject_path.unlink()  # Remove pyproject.toml to test default precedence
    config = _ConfigPyPath(
        context_file=root_path / 'some_file.txt',
        dry_run=True,
        paths=['src'],
        repo_markers={'.git': 'dir'},
    )
    assert config.path_resolution_order == defaults._PATH_RESOLUTION_ORDER, (
        'PATH_RESOLUTION_ORDER_PRECEDENCE_004 path_resolution_order should be '
        f'{defaults._PATH_RESOLUTION_ORDER} from default configuration'
    )
