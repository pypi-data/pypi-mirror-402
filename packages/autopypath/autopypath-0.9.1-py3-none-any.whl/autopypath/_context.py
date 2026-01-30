"""autopypath context information.

Determines the context frame that imported autopypath.
"""

import inspect
from pathlib import Path
from typing import Optional, Union

from ._log import _log


def _context_frameinfo() -> Optional[tuple[Path, str]]:
    """Get the frame info of the context that imported autopypath.

    The context frame is defined as the first frame in the call stack
    that is NOT part of the autopypath module or importlib.

    This function walks the call stack starting from the current frame,
    checking the `__name__` attribute of each frame's globals to determine
    if it belongs to the autopypath module or importlib. When it finds a frame
    that does not belong to these modules, it returns that frame's file path and module name.

    That frame is considered the context frame and its name and file path are returned.

    :return tuple[Path, str] | None: A tuple containing the file path and name
        of the context frame, or None if no such frame is found.
    """
    current_frame = inspect.currentframe()
    try:
        while current_frame is not None:
            frame_name: str = current_frame.f_globals.get('__name__', '')
            _log.debug('inspecting frame: %s', frame_name)
            if not (frame_name.startswith('autopypath') or frame_name.startswith('importlib')):
                context_file: Union[str, None] = current_frame.f_globals.get('__file__')
                if context_file is not None:
                    return (Path(context_file), frame_name)

                # no __file__ in globals.
                else:
                    return None
            current_frame = current_frame.f_back
    finally:
        del current_frame  # Avoid accidental reference cycles
    return None # No context frame found
