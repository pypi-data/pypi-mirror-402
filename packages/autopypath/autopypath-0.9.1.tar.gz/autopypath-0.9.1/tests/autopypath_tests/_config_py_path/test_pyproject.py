"""Tests for the PyProjectConfig class in autopypath._config_py_path._config._pyproject module.

PyProjectConfig is responsible for loading autopypath configuration from pyproject.toml files.

It is a thin subclass of TomlConfig that specifies the correct filename and section for pyproject.toml.

Since the main logic is in TomlConfig, these tests just ensure that PyProjectConfig inherits and
initializes correctly and that __repr__ and __str__ methods work as expected for the subclass.
"""

from collections.abc import Sequence
from pathlib import Path, PosixPath, WindowsPath  # noqa: F401  # Needed for repr eval

from autopypath._config_py_path._config._config import _Config
from autopypath._config_py_path._config._pyproject import _PyProjectConfig
from autopypath._config_py_path._config._toml import _TomlConfig


def test_pyproject_config_init(tmp_path: Path) -> None:
    pyproject_path = tmp_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
""")
    config = _PyProjectConfig(repo_root_path=tmp_path)
    assert isinstance(config, _PyProjectConfig), 'PYPROJECT_001 Expected config to be an instance of PyProjectConfig'
    assert isinstance(config, _TomlConfig), 'PYPROJECT_002 Expected config to be an instance of TomlConfig'
    assert isinstance(config, _Config), 'PYPROJECT_003 Expected config to be an instance of Config'
    assert config.repo_markers is None, 'PYPROJECT_004 Expected repo_markers to be None for empty config'
    assert config.paths is None, 'PYPROJECT_005 Expected paths to be None for empty config'
    assert config.load_strategy is None, 'PYPROJECT_006 Expected load_strategy to be None for empty config'
    assert config.path_resolution_order is None, (
        'PYPROJECT_007 Expected path_resolution_order to be None for empty config'
    )


def test_pyproject_config_repr(tmp_path: Path) -> None:
    pyproject_path = tmp_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
""")
    config = _PyProjectConfig(repo_root_path=tmp_path)
    class_name = config.__class__.__name__
    expected_repr = f'{class_name}(repo_root_path={tmp_path!r})'
    assert repr(config) == expected_repr, 'PYPROJECT_008 __repr__ output does not match expected format'

    new_config = eval(repr(config))
    assert new_config == config, 'PYPROJECT_009 Evaluated __repr__ output does not produce equal object value'


def test_pyproject_config_str(tmp_path: Path) -> None:
    pyproject_path = tmp_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
""")
    config = _PyProjectConfig(repo_root_path=tmp_path)
    class_name = config.__class__.__name__
    expected_str = f'{class_name}(repo_root_path={tmp_path!r})'
    assert str(config) == expected_str, 'PYPROJECT_010 __str__ output does not match expected format'


def test_pyproject_config_paths(tmp_path: Path) -> None:
    # Create pyproject.toml with autopypath configuration
    pyproject_path = tmp_path / 'pyproject.toml'
    pyproject_path.write_text("""
[tool.autopypath]
paths = ["src", "tests"]
""")
    config = _PyProjectConfig(repo_root_path=tmp_path)
    assert isinstance(config.paths, Sequence), (
        f'PYPROJECT_011 Expected paths to be a sequence type: {type(config.paths)!r}'
    )
    assert len(config.paths) == 2, f'PYPROJECT_012 Expected paths list to have length 2: {config.paths!r}'
    assert str(config.paths[0].name) == 'src', 'PYPROJECT_013 Expected first path to be "src"'
    assert str(config.paths[1].name) == 'tests', 'PYPROJECT_014 Expected second path to be "tests"'
    assert config.paths[0] == tmp_path / 'src', 'PYPROJECT_015 First path does not resolve correctly'
    assert config.paths[1] == tmp_path / 'tests', 'PYPROJECT_016 Second path does not resolve correctly'
