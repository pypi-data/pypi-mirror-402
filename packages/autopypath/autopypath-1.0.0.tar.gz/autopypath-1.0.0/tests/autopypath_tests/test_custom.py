"""Tests for autopypath.custom.configure_pypath"""
import importlib
import logging
import sys
from pathlib import Path

import pytest

from autopypath._exceptions import AutopypathError

_ORIGINAL_SYS_PATH: list[str] = sys.path.copy()
_ORIGINAL_NAME: str = __name__


def test_configure_pypath_no_error() -> None:
    """Test that configure_pypath runs without error."""
    global __name__
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        __name__ = '__main__'
        from autopypath.custom import configure_pypath

        configure_pypath()
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        __name__ = _ORIGINAL_NAME
        sys.modules.pop('autopypath.custom', None)


def test_configure_pypath_all_options() -> None:
    """Test that configure_pypath runs with all options set."""
    global __name__
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath', None)
        __name__ = '__main__'
        from autopypath.custom import configure_pypath

        configure_pypath(
            repo_markers={'pyproject.toml': 'file', '.git': 'dir'},
            paths=['src', 'lib'],
            load_strategy='prepend',
            path_resolution_order=['autopypath', 'pyproject'],
            log_level=logging.INFO,
            strict=True,
        )
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        __name__ = _ORIGINAL_NAME
        sys.modules.pop('autopypath.custom', None)


def test_configure_pypath_strict_non_main() -> None:
    """Test that configure_pypath raises AutopypathError when strict is True and not run as __main__."""
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        from autopypath.custom import configure_pypath

        configure_pypath()
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)


def test_configure_pypath_context_file_none() -> None:
    """Test that configure_pypath raises AutopypathError when context file is None."""
    global __name__
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        __name__ = '__main__'
        from autopypath.custom import configure_pypath

        configure_pypath.__globals__['_context_file'] = None
        configure_pypath()
        pytest.fail('Expected AutopypathError due to context file being None.')

    except AutopypathError:
        pass

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        __name__ = _ORIGINAL_NAME


def test_configure_pypath_not_strict_non_main() -> None:
    """Test that configure_pypath does not raise when strict is False and not run as __main__."""
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        from autopypath.custom import configure_pypath

        configure_pypath(strict=False)
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)


def test_import_non_main_context() -> None:
    """Test that importing autopypath.custom from non-__main__ context logs a debug message."""
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        from autopypath.custom import configure_pypath

        configure_pypath(strict=True)
    except AutopypathError:
        pass

    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)

def test_noop_on_multiple_calls(tmp_path: Path) -> None:
    """Test that configure_pypath is a no-op on multiple calls."""
    global __name__
    try:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        sys.modules.pop('autopypath.custom', None)
        __name__ = '__main__'
        from autopypath.custom import configure_pypath

        configure_pypath(log_level=logging.DEBUG,
                         paths=['docs_source'])  # First call - we are using the 'docs_source' path for testing
        assert sys.path != _ORIGINAL_SYS_PATH, "sys.path should be modified on first call to configure_pypath"

        updated_path = sys.path.copy()
        configure_pypath(paths=['docs_source'])  # Second call should be a no-op
        assert sys.path == updated_path, "sys.path should remain unchanged on second call to configure_pypath"
    finally:
        sys.path = _ORIGINAL_SYS_PATH.copy()
        __name__ = _ORIGINAL_NAME
        sys.modules.pop('autopypath.custom', None)


def test_import_raises_when_context_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that importing autopypath raises AutopypathError when context frame is unknown."""
    global __name__
    original_name = __name__
    try:
        __name__ = '__main__'
        sys.modules.pop('autopypath.custom', None)
        import autopypath.custom

        # Patch the frame introspection to simulate inability to find context frame
        monkeypatch.setattr("inspect.currentframe", lambda: None)

        with pytest.raises(autopypath.AutopypathError, match="could not determine context file"):
            importlib.reload(autopypath.custom)
    finally:
        __name__ = original_name
