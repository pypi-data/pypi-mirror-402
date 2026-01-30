"""Test context detection functionality."""

import inspect
from pathlib import Path
from types import FrameType
from typing import Union

import pytest

from autopypath._context import _context_frameinfo


def test_context_frameinfo_basic() -> None:
    """Test that the context frame info is correctly identified."""
    context_info = _context_frameinfo()
    assert context_info is not None, 'CONTEXT_001 Context frame info should not be None'
    context_path, context_name = context_info
    assert isinstance(context_path, type(Path())), 'CONTEXT_002 Context path should be a Path object'
    assert isinstance(context_name, str), 'CONTEXT_003 Context name should be a string'
    # The test file itself should be the context
    assert context_name == __name__, 'CONTEXT_004 Context name should match the test module name'
    assert context_path.name == 'test_context.py', 'CONTEXT_005 Context path should point to this test file'


def test_context_frameinfo_no_autopypath() -> None:
    """Test that the context frame info is identified when autopypath is not in the stack."""

    def dummy_function() -> Union[tuple[Path, str], None]:
        return _context_frameinfo()

    context_info = dummy_function()
    assert context_info is not None, 'CONTEXT_006 Context frame info should not be None'
    context_path, context_name = context_info
    assert context_name == __name__, 'CONTEXT_007 Context name should match the test module name'
    assert context_path.name == 'test_context.py', 'CONTEXT_008 Context path should point to this test file'


def test_context_frameinfo_currentframe_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _context_frameinfo returns None if inspect.currentframe() is None."""
    from autopypath._context import _context_frameinfo

    monkeypatch.setattr(inspect, 'currentframe', lambda: None)
    result = _context_frameinfo()
    assert result is None, 'CONTEXT_009 Should return None if currentframe() is None'


def test_context_frameinfo_no_file_in_globals(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _context_frameinfo returns None if __file__ is missing."""
    class DummyCode:
        co_name = "dummy"

    class DummyFrame:
        f_globals = {"__name__": "dummy"}  # no __file__
        f_code = DummyCode()
        f_back: Union[FrameType, None] = None

    monkeypatch.setattr(inspect, "currentframe", lambda: DummyFrame())
    result = _context_frameinfo()
    assert result is None, "CONTEXT_010 Should return None if __file__ is missing in globals"
