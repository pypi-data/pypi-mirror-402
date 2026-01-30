"""Tests for the AutopypathConfig class in autopypath._config_py_path._config._autopypath module.

AutopypathConfig is responsible for loading autopypath configuration from autopypath.toml files.

It is a thin subclass of TomlConfig that specifies the correct filename and section for autopypath.toml.

Since the main logic is in TomlConfig, these tests just ensure that AutopypathConfig inherits and
initializes correctly and that __repr__ and __str__ methods work as expected for the subclass.
"""

from pathlib import Path, PosixPath, WindowsPath  # noqa: F401  # Needed for repr eval

from autopypath._config_py_path._config._autopypath import _AutopypathConfig
from autopypath._config_py_path._config._config import _Config
from autopypath._config_py_path._config._toml import _TomlConfig


def test_autopypath_config_init(tmp_path: Path) -> None:
    autopypath_path = tmp_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
""")
    config = _AutopypathConfig(repo_root_path=tmp_path)
    assert isinstance(config, _AutopypathConfig), 'AUTOPYPATH_001 Expected config to be an instance of AutopypathConfig'
    assert isinstance(config, _TomlConfig), 'AUTOPYPATH_002 Expected config to be an instance of TomlConfig'
    assert isinstance(config, _Config), 'AUTOPYPATH_003 Expected config to be an instance of Config'
    assert config.repo_markers is None, 'AUTOPYPATH_004 Expected repo_markers to be None for empty config'
    assert config.paths is None, 'AUTOPYPATH_005 Expected paths to be None for empty config'
    assert config.load_strategy is None, 'AUTOPYPATH_006 Expected load_strategy to be None for empty config'
    assert config.path_resolution_order is None, (
        'AUTOPYPATH_007 Expected path_resolution_order to be None for empty config'
    )


def test_autopypath_config_repr(tmp_path: Path) -> None:
    autopypath_path = tmp_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
""")
    config = _AutopypathConfig(repo_root_path=tmp_path)
    class_name = config.__class__.__name__
    expected_repr = f'{class_name}(repo_root_path={tmp_path!r})'
    assert repr(config) == expected_repr, (
        'AUTOPYPATH_008 __repr__ output does not match expected format:'
        f' expected {expected_repr!r}, got {repr(config)!r}'
    )

    new_config = eval(repr(config))
    assert new_config == config, 'AUTOPYPATH_009 Evaluated __repr__ output does not produce equal object value'


def test_autopypath_config_str(tmp_path: Path) -> None:
    autopypath_path = tmp_path / 'autopypath.toml'
    autopypath_path.write_text("""
[tool.autopypath]
""")
    config = _AutopypathConfig(repo_root_path=tmp_path)
    class_name = config.__class__.__name__
    expected_str = f'{class_name}(repo_root_path={tmp_path!r})'
    assert str(config) == expected_str, 'AUTOPYPATH_010 __str__ output does not match expected format'
