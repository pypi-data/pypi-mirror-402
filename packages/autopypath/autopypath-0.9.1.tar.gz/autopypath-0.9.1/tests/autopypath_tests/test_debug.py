"""Tests for :mod:`autopypath.debug` module."""

import importlib
import logging
import sys
from pathlib import Path

import pytest


def test_autopypath_import_log_level(tmp_path: Path) -> None:
    """Test that importing autopypath sets log level to INFO."""
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    autopypath_toml_path = repo_path / 'autopypath.toml'
    autopypath_toml_path.write_text("""
[tool.autopypath]
paths = ["src", "tests"]
load_strategy = "prepend"
path_resolution_order = ["manual", "autopypath"]
repo_markers = {".git" = "dir", "autopypath.toml" = "file"}
""")

    sys.modules.pop('autopypath.debug', None)
    import autopypath.debug
    from autopypath._log import _log

    assert _log.level == logging.DEBUG, (
        'AUTOPYPATH_001 Log level should be set to DEBUG upon importing autopypath.debug')
    assert autopypath.debug._context_name != '__main__', (
        'AUTOPYPATH_002 autopypath.debug._context_name should not be __main__ when imported from inside a function; '
        f'got context name: {autopypath.debug._context_name!r}'
    )
    assert autopypath.debug._path_adjusted is False, (
        'AUTOPYPATH_003 autopypath.debug._path_adjusted should be False when autopypath is '
        'imported from non-__main__ context.'
    )


def test_forced_main_execution(tmp_path: Path) -> None:
    """Test autopypath behavior when run as __main__."""

    # "Do not cite the Deep Magic to me, Witch! I was there when it was written."
    #
    # The following code forcibly sets __name__ to '__main__' to simulate running as a script.
    # This is deep magic and should not be used outside of testing and might break in future Python versions.
    # It has been tested on Python 3.9 through 3.14, and PyPy 3.10 and 3.11 as of Jan. 2026

    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    autopypath_toml_path = repo_path / 'autopypath.toml'
    autopypath_toml_path.write_text("""
[tool.autopypath]
paths = ["src", "tests"]
load_strategy = "prepend"
path_resolution_order = ["manual", "autopypath"]
repo_markers = {".git" = "dir", "autopypath.toml" = "file"}
""")

    # We do some shenanigans here to forcibly reload autopypath with __name__ set to '__main__'.

    # "Do not cite the Deep Magic to me, Witch! I was there when it was written."
    #
    # The following code forcibly sets __name__ to '__main__' to simulate running as a script.
    # This is deep magic and should not be used outside of testing and may break in future Python versions.
    # It has been tested on Python 3.9 through 3.14, and PyPy 3.10 and 3.11 as of Jan. 2026
    global __name__
    original_name = __name__
    try:
        __name__ = '__main__'
        sys.modules.pop('autopypath.debug', None)
        import autopypath.debug
        from autopypath._log import _log
    finally:
        __name__ = original_name

    assert _log.level == logging.DEBUG, (
        'AUTOPYPATH_001 Log level should be set to DEBUG upon importing autopypath.debug')
    assert autopypath.debug._context_name == '__main__', (
        'AUTOPYPATH_002 autopypath.debug._context_name should be __main__ because we invoked deep magic; '
        f'got context name: {autopypath.debug._context_name!r}'
    )
    assert autopypath.debug._path_adjusted is True, (
        'AUTOPYPATH_003 autopypath.debug._path_adjusted should be True when autopypath is '
        'imported from our forced __main__ context.'
    )


def test_import_raises_when_context_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that importing autopypath raises AutopypathError when context frame is unknown."""
    global __name__
    original_name = __name__
    try:
        __name__ = '__main__'
        sys.modules.pop('autopypath.debug', None)
        import autopypath.debug

        # Patch the frame introspection to simulate inability to find context frame
        monkeypatch.setattr("inspect.currentframe", lambda: None)

        with pytest.raises(autopypath.AutopypathError, match="could not determine context file"):
            importlib.reload(autopypath.debug)
    finally:
        __name__ = original_name


# For direct manual execution of tests as a script.
#
# This is what pytest would do to set up sys.path for testing when run from the command line,
# and what autopypath is supposed to help with by removing the need for hardcoding manually
# determined sys.path tweaks that have to be made on a script-by-script basis.
#
# Note that when run via pytest, __name__ will NOT be '__main__', so autopypath
# will not adjust sys.path automatically during the test runs.
#
# When using autopypath in real scripts, it adjusts sys.path automatically
# when the script is run directly (i.e., when __name__ == '__main__')
# without needing any special test harness code to set up sys.path.
#
# It becomes part of your script like this:
#
#   import autopypath.debug
#   import pytest
#
#   # rest of your script code here
#
#   if __name__ == '__main__':
#       pytest.main(__file__)
#
# And it **just works** when run directly at the command line as `python your_script.py`
#
if __name__ == '__main__':
    repo_dir = Path(__file__).parent.parent
    sys.path = [str(repo_dir / 'src'), str(repo_dir / 'tests')] + sys.path

    pytest.main([__file__])
