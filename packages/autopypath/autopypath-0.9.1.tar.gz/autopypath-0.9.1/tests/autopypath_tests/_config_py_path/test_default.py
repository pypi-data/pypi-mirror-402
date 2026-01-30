"""Tests for autopypath._config_py_path._config._manual module.

The Manual config class is just no changes subclass of
the base Config class, so this test just verifies that the
class can be instantiated as ManualConfig and is a subclass
of Config.

All the real logic is tested in tests/_config_py_path/test_config.py
"""

from autopypath import _defaults
from autopypath._config_py_path._config import _Config, _DefaultConfig


def test_default_config_init() -> None:
    """Test that DefaultConfig can be instantiated with default parameters."""
    config = _DefaultConfig()

    assert isinstance(config, _DefaultConfig), 'DEFAULT_001 Failed to instantiate DefaultConfig'
    assert issubclass(_DefaultConfig, _Config), 'DEFAULT_002 DefaultConfig is not a subclass of Config'
    assert config.load_strategy == _defaults._LOAD_STRATEGY, 'DEFAULT_003 Load strategy does not match default'
    assert config.paths == _defaults._PATHS, 'DEFAULT_004 Paths do not match default'
    assert config.repo_markers == _defaults._REPO_MARKERS, 'DEFAULT_005 Repo markers do not match default'
    assert config.path_resolution_order == _defaults._PATH_RESOLUTION_ORDER, (
        'DEFAULT_006 Path resolution order does not match default'
    )


def test_repr() -> None:
    """Test Config __repr__ method."""
    # Note - use of eval on the repr output to reconstitute the Config instance
    # and compare to the original. This is safe in this controlled test context
    # where we know the input values and expected output. In general, eval
    # should be avoided due to security risks. IOW: This is a test-only use of eval.
    config = _DefaultConfig()

    reconstituted_config = eval(repr(config))
    assert reconstituted_config == config, (
        'REPR_001 Reconstituted Config from __repr__ does not match original. '
        f'Original: {config!r}, Reconstituted: {reconstituted_config!r}'
    )
