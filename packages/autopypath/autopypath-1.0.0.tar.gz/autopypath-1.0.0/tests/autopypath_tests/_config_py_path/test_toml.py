from collections.abc import Sequence
from pathlib import Path, PosixPath, WindowsPath  # noqa: F401  # Needed for repr eval

import pytest

from autopypath._config_py_path._config._toml import _TomlConfig
from autopypath._exceptions import AutopypathError
from autopypath._marker_type import _MarkerType


def test_toml_config_init(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    marker_file = repo_root / 'filename.txt'
    marker_file.touch()
    marker_dir = repo_root / 'dirname'
    marker_dir.mkdir()
    (repo_root / 'src').mkdir()  # One of the two default paths so we can test both with and without presence
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
load_strategy = 'prepend'
path_resolution_order = ['manual', 'autopypath', 'pyproject']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except Exception as e:
        pytest.fail(f'TOML_001 Initialization of TomlConfig failed with exception: {e}')


def test_toml_missing_section(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.other_tool]
paths = ['src', 'lib']
""")

    config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    assert config.load_strategy is None, 'TOML_002 Expected load_strategy to be None when section is missing'
    assert config.paths is None, 'TOML_003 Expected paths to be None when section is missing'
    assert config.path_resolution_order is None, (
        'TOML_004 Expected path_resolution_order to be None when section is missing'
    )
    assert config.repo_markers is None, 'TOML_005 Expected marker_files to be None when section is missing'


def test_toml_missing_file(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()

    toml_filename = 'non_existent.toml'
    config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    assert config.no_file_found, 'TOML_MISSING_001 Expected no_file_found to be True when TOML file does not exist'


def test_toml_invalid_repo_marker_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = 'should_be_a_table_not_a_string'
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_007 Expected AutopypathError when repo_markers has invalid syntax')


def test_toml_invalid_path_resolution_order_value(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
path_resolution_order = ['invalid_value']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_008 Expected AutopypathError when path_resolution_order has an invalid value')


def test_toml_invalid_load_strategy_value(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
load_strategy = 'invalid_strategy'
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_009 Expected AutopypathError when load_strategy has an invalid value')


def test_toml_invalid_load_strategy_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
load_strategy = ['should_be_a_string_not_a_list']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_010 Expected AutopypathError when load_strategy has invalid syntax')


def test_toml_invalid_paths_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = 'should_be_a_list_not_a_string'
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_011 Expected AutopypathError when paths has invalid syntax')


def test_toml_invalid_repo_markers_value(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = {'.git': 'should_be_MarkerType_not_general_string'}
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_012 Expected AutopypathError when repo_markers has an invalid value')


def test_toml_invalid_paths_value(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 123]
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_013 Expected AutopypathError when paths has an invalid type of value')


def test_toml_invalid_path_resolution_order_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
path_resolution_order = 'should_be_a_list_not_a_string'
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_014 Expected AutopypathError when path_resolution_order has invalid syntax')


def test_toml_invalid_repo_markers_filename_type(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = {123='DIR'}
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_015 Expected AutopypathError when repo_markers has an invalid type for the filename')


def test_toml_invalid_repo_markers_filename_value(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = {'*invalid*': 'DIR'}
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_016 Expected AutopypathError when repo_markers has an invalid filename value')


def test_toml_misconfigured_section_name(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool..autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_017 Expected AutopypathError when toml_section has an invalid syntax')


def test_toml_incorrect_section_table_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""

[tool]

autopypath = 'hello'

""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_018 Expected AutopypathError when toml_section is misdefined in the TOML file')


def test_toml_repo_markers_table_syntax(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = ['.git', 'DIR', 'setup.py', 'FILE']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_019 Expected AutopypathError when repo_markers is not a table/dictionary')


def test_toml_repo_markers_table_value_type(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = {'.git'=['should_be_string_not_list']}
""")
    try:
        config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
        pytest.fail('TOML_020 Expected AutopypathError when repo_markers has '
                    f'non-string value type: {config.repo_markers}')
    except AutopypathError:
        pass


def test_toml_repr(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""[tool.autopypath]
paths = ['src', 'lib']
""")
    config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    repr_str = repr(config)
    assert 'TomlConfig' in repr_str, 'TOML_021 Expected __repr__ to contain class name'
    assert 'paths' in repr_str, 'TOML_022 Expected __repr__ to contain paths attribute'
    assert 'repo_markers' in repr_str, 'TOML_023 Expected __repr__ to contain repo_markers attribute'
    assert 'load_strategy' in repr_str, 'TOML_024 Expected __repr__ to contain load_strategy attribute'
    assert 'path_resolution_order' in repr_str, 'TOML_025 Expected __repr__ to contain path_resolution_order attribute'
    try:
        round_trip_config = eval(repr_str)
    except Exception as e:
        pytest.fail(f'TOML_026 Expected __repr__ to be evaluable without exception, but got: {e}\nRepr: {repr_str}')
    assert round_trip_config == config, (
        f'TOML_027 Expected __repr__ to be evaluable to the same object value: {repr_str}'
    )


def test_toml_str(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""[tool.autopypath]
paths = ['src', 'lib']
""")
    config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    str_repr = str(config)
    assert 'TomlConfig' in str_repr, 'TOML_028 Expected __str__ to contain class name'
    assert 'paths' in str_repr, 'TOML_029 Expected __str__ to contain paths attribute'
    assert 'repo_markers' in str_repr, 'TOML_030 Expected __str__ to contain repo_markers attribute'
    assert 'load_strategy' in str_repr, 'TOML_031 Expected __str__ to contain load_strategy attribute'
    assert 'path_resolution_order' in str_repr, 'TOML_032 Expected __str__ to contain path_resolution_order attribute'


def test_toml_good_repo_markers(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
repo_markers = {'.git'='dir', 'setup.py'='file'}
""")
    try:
        config = _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except Exception as e:
        pytest.fail(f'TOML_033 Initialization of TomlConfig with valid repo_markers failed with exception: {e}')
    assert config.repo_markers == {'.git': _MarkerType.DIR, 'setup.py': _MarkerType.FILE}, (
        f'TOML_034 Expected repo_markers to be correctly parsed, got: {config.repo_markers}'
    )


def test_toml_filename_value(tmp_path: Path) -> None:
    """Test that providing an invalid toml_filename raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml '  # Exists, but invalid name due to trailing space
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")

    toml_section = 'tool.autopypath'
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section=toml_section)
    except AutopypathError:
        return
    pytest.fail('TOML_035 Expected AutopypathError when toml_filename has invalid value')


def test_toml_filename_type(tmp_path: Path) -> None:
    """Test that providing a non-string toml_filename raises AutopypathError."""
    toml_section = 'tool.autopypath'

    # Create a temporary TOML file to satisfy the existence check
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")

    bad_toml_filename = 123  # Invalid type

    try:
        _TomlConfig(
            repo_root_path=repo_root,
            toml_filename=bad_toml_filename,  # type: ignore
            toml_section=toml_section,
        )
    except AutopypathError:
        return
    pytest.fail('TOML_036 Expected AutopypathError when toml_filename has invalid type')


def test_tome_filename_not_toml_suffix(tmp_path: Path) -> None:
    """Test that providing a toml_filename without .toml suffix raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'config.txt'  # Invalid suffix
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")
    toml_section = 'tool.autopypath'

    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section=toml_section)
    except AutopypathError:
        return
    pytest.fail('TOML_037 Expected AutopypathError when toml_filename does not have .toml suffix')


def test_toml_section_cannot_be_empty_string(tmp_path: Path) -> None:
    """Test that providing an empty string for toml_section raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")
    bad_toml_section = ''  # Invalid empty string for section name
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section=bad_toml_section)
    except AutopypathError:
        return
    pytest.fail('TOML_038 Expected AutopypathError when toml_section is an empty string')


def test_toml_section_type(tmp_path: Path) -> None:
    """Test that providing a non-string toml_section raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")
    bad_toml_section = 456  # Invalid type for section name
    try:
        _TomlConfig(
            repo_root_path=repo_root,
            toml_filename=toml_filename,
            toml_section=bad_toml_section,  # type: ignore
        )
    except AutopypathError:
        return
    pytest.fail('TOML_039 Expected AutopypathError when toml_section has invalid type')


def test_toml_section_invalid_adjacent_dots(tmp_path: Path) -> None:
    """Test that providing a toml_section with adjacent special chars raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""
[tool.autopypath]
paths = ['src', 'lib']
""")
    bad_passed_sections: list[str] = []
    for bad_toml_section in [
        'tool..autopypath',
        'tool.-autopypath',
        'tool._autopypath',
        'tool--autopypath',
        'tool-.autopypath',
        'tool-_autopypath',
        'tool__autopypath',
        'tool_.autopypath',
        'tool_-autopypath',
    ]:
        try:
            _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section=bad_toml_section)
        except AutopypathError:
            continue
        bad_passed_sections.append(bad_toml_section)
    if bad_passed_sections:
        bad_items = f'{bad_passed_sections!r}'
        pytest.fail(
            'TOML_040 Expected AutopypathError when toml_section is invalid: '
            f'{bad_items} unexpectedly passed validation.'
        )


def test_toml_section_invalid_start_end_chars(tmp_path: Path) -> None:
    """Test that providing a toml_section with invalid start/end chars raises AutopypathError."""
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""[tool.autopypath]
paths = ['src', 'lib']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='-tool.autopypath')
    except AutopypathError:
        return

    pytest.fail('TOML_041 Expected AutopypathError when toml_section starts with invalid character')


def test_toml_repo_root_path_is_none() -> None:
    """Test that providing None for repo_root_path creates special behavior."""
    toml_filename = 'toml_file.toml'
    toml_section = 'tool.autopypath'

    config = _TomlConfig(repo_root_path=None, toml_filename=toml_filename, toml_section=toml_section)

    assert config.paths is None, 'TOML_042 Expected paths to be None when repo_root_path is None'
    assert config.repo_markers is None, 'TOML_043 Expected repo_markers to be None when repo_root_path is None'
    assert config.load_strategy is None, 'TOML_044 Expected load_strategy to be None when repo_root_path is None'
    assert config.path_resolution_order is None, (
        'TOML_045 Expected path_resolution_order to be None when repo_root_path is None'
    )
    assert str(config.toml_filepath) == '<_NoPath>', (
        'TOML_046 Expected toml_filepath to be <_NoPath> when repo_root_path is None'
    )
    assert config.toml_section == toml_section, (
        'TOML_047 Expected toml_section to be set correctly even when repo_root_path is None'
    )


def test_toml_config_paths(tmp_path: Path) -> None:
    # Create toml file with autopypath configuration
    src_path = tmp_path / 'src'
    tests_path = tmp_path / 'tests'
    toml_path = tmp_path / 'config.toml'
    toml_path.write_text("""
[tool.autopypath]
paths = ["src", "tests"]
""")
    config = _TomlConfig(repo_root_path=tmp_path, toml_filename='config.toml', toml_section='tool.autopypath')
    assert isinstance(config.paths, Sequence), 'TOML_048 Expected paths to be a sequence type'
    assert len(config.paths) == 2, 'TOML_049 Expected paths list to have length 2'
    assert str(config.paths[0].name) == 'src', 'TOML_050 Expected first path to be "src"'
    assert str(config.paths[1].name) == 'tests', 'TOML_051 Expected second path to be "tests"'
    assert config.paths[0] == src_path, 'TOML_052 Expected first path to be match the path to src directory'
    assert config.paths[1] == tests_path, 'TOML_053 Expected second path to be match the path to tests directory'

def test_toml_path_cannot_contain_backslashes(tmp_path: Path) -> None:
    repo_root = tmp_path / 'my_repo'
    repo_root.mkdir()
    toml_filename = 'toml_file.toml'
    toml_path = repo_root / toml_filename
    toml_path.write_text("""[tool.autopypath]
paths = ['src\\lib']
""")
    try:
        _TomlConfig(repo_root_path=repo_root, toml_filename=toml_filename, toml_section='tool.autopypath')
    except AutopypathError:
        return
    pytest.fail('TOML_054 Expected AutopypathError when path contains backslashes')
