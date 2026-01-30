"""Tests for the _NoPath type in autopypath.types._no_path module."""
# mypy: disable-error-code=operator
# pyright: reportCallIssue=false

import os

import pytest

from autopypath._types._no_path import _NOT_SUPPORTED_ERR, _NoPath, _NotSupported, _UsagePreventedType


@pytest.fixture
def no_path() -> _NoPath:
    return _NoPath()


def test_exists_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.exists(_UsagePreventedType())
    assert True, 'NOPATH_001: exists should raise NotSupported'


def test_is_file_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_file(_UsagePreventedType())
    assert True, 'NOPATH_002: is_file should raise NotSupported'


def test_is_dir_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_dir(_UsagePreventedType())
    assert True, 'NOPATH_003: is_dir should raise NotSupported'


def test_open_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.open(_UsagePreventedType())
    assert True, 'NOPATH_004: open should raise NotSupported'


def test_read_text_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.read_text(_UsagePreventedType())
    assert True, 'NOPATH_005: read_text should raise NotSupported'


def test_read_bytes_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.read_bytes(_UsagePreventedType())
    assert True, 'NOPATH_006: read_bytes should raise NotSupported'


def test_write_text_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.write_text(_UsagePreventedType())
    assert True, 'NOPATH_007: write_text should raise NotSupported'


def test_write_bytes_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.write_bytes(_UsagePreventedType())
    assert True, 'NOPATH_008: write_bytes should raise NotSupported'


def test_mkdir_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.mkdir(_UsagePreventedType())
    assert True, 'NOPATH_009: mkdir should raise NotSupported'


def test_rmdir_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.rmdir(_UsagePreventedType())
    assert True, 'NOPATH_010: rmdir should raise NotSupported'


def test_unlink_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.unlink(_UsagePreventedType())
    assert True, 'NOPATH_011: unlink should raise NotSupported'


def test_rename_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.rename(_UsagePreventedType())
    assert True, 'NOPATH_012: rename should raise NotSupported'


def test_replace_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.replace(_UsagePreventedType())
    assert True, 'NOPATH_013: replace should raise NotSupported'


def test_touch_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.touch(_UsagePreventedType())
    assert True, 'NOPATH_014: touch should raise NotSupported'


def test_stat_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.stat(_UsagePreventedType())
    assert True, 'NOPATH_015: stat should raise NotSupported'


def test_chmod_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.chmod(_UsagePreventedType())
    assert True, 'NOPATH_016: chmod should raise NotSupported'


def test_lstat_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.lstat(_UsagePreventedType())
    assert True, 'NOPATH_017: lstat should raise NotSupported'


def test_owner_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.owner(_UsagePreventedType())
    assert True, 'NOPATH_018: owner should raise NotSupported'


def test_group_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.group(_UsagePreventedType())
    assert True, 'NOPATH_019: group should raise NotSupported'


def test_readlink_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.readlink(_UsagePreventedType())
    assert True, 'NOPATH_020: readlink should raise NotSupported'


def test_symlink_to_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.symlink_to(_UsagePreventedType())
    assert True, 'NOPATH_021: symlink_to should raise NotSupported'


def test_hardlink_to_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.hardlink_to(_UsagePreventedType())
    assert True, 'NOPATH_022: hardlink_to should raise NotSupported'


def test_absolute_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.absolute(_UsagePreventedType())
    assert True, 'NOPATH_023: absolute should raise NotSupported'


def test_resolve_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.resolve(_UsagePreventedType())
    assert True, 'NOPATH_024: resolve should raise NotSupported'


def test_samefile_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.samefile(_UsagePreventedType())
    assert True, 'NOPATH_025: samefile should raise NotSupported'


def test_expanduser_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.expanduser(_UsagePreventedType())
    assert True, 'NOPATH_026: expanduser should raise NotSupported'


def test_with_name_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.with_name(_UsagePreventedType())
    assert True, 'NOPATH_027: with_name should raise NotSupported'


def test_with_suffix_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.with_suffix(_UsagePreventedType())
    assert True, 'NOPATH_028: with_suffix should raise NotSupported'


def test_relative_to_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.relative_to(_UsagePreventedType())
    assert True, 'NOPATH_029: relative_to should raise NotSupported'


def test_is_absolute_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_absolute(_UsagePreventedType())
    assert True, 'NOPATH_030: is_absolute should raise NotSupported'


def test_is_reserved_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_reserved(_UsagePreventedType())
    assert True, 'NOPATH_031: is_reserved should raise NotSupported'


def test_joinpath_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.joinpath(_UsagePreventedType())
    assert True, 'NOPATH_032: joinpath should raise NotSupported'


def test_match_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.match(_UsagePreventedType())
    assert True, 'NOPATH_033: match should raise NotSupported'


def test_parent_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.parent
    assert True, 'NOPATH_034: parent should raise NotSupported'


def test_parents_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.parents
    assert True, 'NOPATH_035: parents should raise NotSupported'


def test_parts_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.parts
    assert True, 'NOPATH_036: parts should raise NotSupported'


def test_drive_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.drive
    assert True, 'NOPATH_037: drive should raise NotSupported'


def test_root_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.root
    assert True, 'NOPATH_038: root should raise NotSupported'


def test_anchor_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.anchor
    assert True, 'NOPATH_039: anchor should raise NotSupported'


def test_name_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.name
    assert True, 'NOPATH_040: name should raise NotSupported'


def test_suffix_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.suffix
    assert True, 'NOPATH_041: suffix should raise NotSupported'


def test_suffixes_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.suffixes
    assert True, 'NOPATH_042: suffixes should raise NotSupported'


def test_stem_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path.stem
    assert True, 'NOPATH_043: stem should raise NotSupported'


def test_as_posix_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.as_posix(_UsagePreventedType())
    assert True, 'NOPATH_044: as_posix should raise NotSupported'


def test_as_uri_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.as_uri(_UsagePreventedType())
    assert True, 'NOPATH_045: as_uri should raise NotSupported'


def test_is_mount_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_mount(_UsagePreventedType())
    assert True, 'NOPATH_046: is_mount should raise NotSupported'


def test_is_symlink_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_symlink(_UsagePreventedType())
    assert True, 'NOPATH_047: is_symlink should raise NotSupported'


def test_is_block_device_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_block_device(_UsagePreventedType())
    assert True, 'NOPATH_048: is_block_device should raise NotSupported'


def test_is_char_device_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_char_device(_UsagePreventedType())
    assert True, 'NOPATH_049: is_char_device should raise NotSupported'


def test_is_fifo_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_fifo(_UsagePreventedType())
    assert True, 'NOPATH_050: is_fifo should raise NotSupported'


def test_is_socket_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.is_socket(_UsagePreventedType())
    assert True, 'NOPATH_051: is_socket should raise NotSupported'


def test_iterdir_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.iterdir(_UsagePreventedType())
    assert True, 'NOPATH_052: iterdir should raise NotSupported'


def test_glob_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.glob(_UsagePreventedType())
    assert True, 'NOPATH_053: glob should raise NotSupported'


def test_rglob_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.rglob(_UsagePreventedType())
    assert True, 'NOPATH_054: rglob should raise NotSupported'


def test_cwd_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.cwd()
    assert True, 'NOPATH_055: cwd should raise NotSupported'


def test_home_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        no_path.home()
    assert True, 'NOPATH_056: home should raise NotSupported'


def test_repr_returns_expected(no_path: _NoPath) -> None:
    assert repr(no_path) == '<_NoPath>', 'NOPATH_057: __repr__ should return <_NoPath>'


def test_str_returns_expected(no_path: _NoPath) -> None:
    assert str(no_path) == '<_NoPath>', 'NOPATH_058: __str__ should return <_NoPath>'


def test_eq_returns_true_for_no_path_instances(no_path: _NoPath) -> None:
    other = _NoPath()
    assert no_path == other, 'NOPATH_059: __eq__ should return True for two NoPath instances'


def test_eq_returns_false_for_non_no_path(no_path: _NoPath) -> None:
    assert not (no_path == object()), 'NOPATH_060: __eq__ should return False for non-NoPath objects'


def test_fspath_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        os.fspath(no_path)
    assert True, 'NOPATH_061: __fspath__ should raise NotSupported'


def test_truediv_raises(no_path: _NoPath) -> None:
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = no_path / 'anything'
    assert True, 'NOPATH_062: __truediv__ should raise NotSupported'


def test_rtruediv_raises(no_path: _NoPath) -> None:
    # Use an int LHS so Python will try rhs.__rtruediv__ after int.__truediv__ returns NotImplemented.
    with pytest.raises(_NotSupported, match=_NOT_SUPPORTED_ERR):
        _ = 1 / no_path
    assert True, 'NOPATH_063: __rtruediv__ should raise NotSupported'


def test_hash_is_constant_and_set_dedupes(no_path: _NoPath) -> None:
    assert hash(no_path) == 0, 'NOPATH_064: __hash__ should return 0'
    assert len({no_path, _NoPath()}) == 1, 'NOPATH_065: equal _NoPath instances should dedupe in a set'
