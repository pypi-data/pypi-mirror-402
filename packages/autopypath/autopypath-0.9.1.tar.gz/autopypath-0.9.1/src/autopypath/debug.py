"""Enables debug logging for autopypath when imported.

**Automatic Debug Mode**
------------------------
By importing the :mod:`autopypath.debug` submodule instead of :mod:`autopypath`,
detailed debug logging is enabled to trace how the project root is determined,
which paths are added to `sys.path`, and any issues encountered along the way.

Additionally, warnings logged by the configuration processing are upgraded to logged errors
and exceptions are raised for them. This does not affect warnings originating from other modules
that autopypath depends on.

It changes the global logging level for the :mod:`autopypath._log` logger to ``DEBUG``.
Normally this should have no side effects because autopypath can only be imported once per process
and does not publically expose any logging configuration APIs.

Otherwise, it is functionally equivalent to importing :mod:`autopypath`.

This is useful for troubleshooting and understanding the internal workings of autopypath.

.. code-block:: python

    import autopypath.debug
    # sys.path was adjusted automatically with debug logging and exceptions enabled

"""

import logging
from pathlib import Path
from typing import Optional

from ._config_py_path import _ConfigPyPath
from ._context import _context_frameinfo
from ._exceptions import AutopypathError
from ._log import _log

__all__ = ['AutopypathError']

_log.setLevel(logging.DEBUG)


_context_file: Optional[Path] = None
"""This is the file path of the script that imported this module, if available."""
_context_name: Optional[str] = None
"""This is the __name__ of the script that imported this module, if available."""
_path_adjusted: bool = False
"""Indicates whether autopypath adjusted sys.path automatically upon import."""

_context_info: Optional[tuple[Path, str]] = _context_frameinfo()
if _context_info is not None:
    _context_file, _context_name = _context_info
    if _context_name != '__main__':
        _log.debug(
            'autopypath imported from non-__main__ context (%s); no sys.path changes will be applied.',
            _context_name,
        )
        _path_adjusted = False
    else:
        _ConfigPyPath(context_file=_context_file, strict=True)
        _log.debug('sys.path adjusted automatically for %s', _context_file)
        _path_adjusted = True
else:
    _log.error('could not determine context file; no sys.path changes will be applied.')
    raise AutopypathError('could not determine context file for autopypath; sys.path not adjusted.')
