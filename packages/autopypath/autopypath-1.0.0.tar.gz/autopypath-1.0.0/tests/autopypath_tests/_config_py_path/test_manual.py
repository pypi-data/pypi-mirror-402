"""Tests for autopypath._config_py_path._config._manual module.

The Manual config class is just no changes subclass of
the base Config class, so this test just verifies that the
class can be instantiated as ManualConfig and is a subclass
of Config.

All the real logic is tested in tests/_config_py_path/test_config.py
"""

from autopypath._config_py_path._config import _Config, _ManualConfig


def test_manual_config_init() -> None:
    """Test that ManualConfig can be instantiated with default parameters."""
    assert isinstance(_ManualConfig(), _ManualConfig), 'MANUAL_001 Failed to instantiate ManualConfig'
    assert issubclass(_ManualConfig, _Config), 'MANUAL_002 ManualConfig is not a subclass of Config'
