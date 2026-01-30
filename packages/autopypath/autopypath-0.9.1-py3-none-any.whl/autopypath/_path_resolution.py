"""Resolution order definitions for autopypath."""

from enum import Enum
from types import MappingProxyType
from typing import Union

from ._typing import Final, Literal, TypeAlias, TypeGuard

__all__ = ['_PathResolution']


class _PathResolution(str, Enum):
    """Defines the order in which :data:`sys.path` sources are resolved.

    - MANUAL: Paths provided directly to the configuration function.
    - AUTOPYPATH: Paths specified in a `autopypath.toml` file.
    - PYPROJECT: Paths specified in `pyproject.toml` in the repository root.

    Example
    -------
    .. code-block:: python
        from autopypath.path_resolution import PathResolution

        order = PathResolution.ENV
    """

    MANUAL = 'manual'
    """Paths provided directly via the `paths` parameter to `configure_pypath()`."""
    AUTOPYPATH = 'autopypath'
    """Paths specified in a `autopypath.toml` file."""
    PYPROJECT = 'pyproject'
    """Paths specified in the [tool.autopypath] section of the `pyproject.toml` file in the repository root."""



PathResolutionLiteral: TypeAlias = Literal['manual', 'autopypath', 'pyproject']
"""Literal type for PathResolution values."""


PATH_RESOLUTION_MAP: Final[MappingProxyType[PathResolutionLiteral, _PathResolution]] = MappingProxyType(
    {order.value: order for order in _PathResolution}
)
"""Mapping from literal strings to PathResolution enum members.

Example
-------

.. code-block:: python

    from autopypath.path_resolution import RESOLUTION_ORDER_MAP, PathResolution

    order = RESOLUTION_ORDER_MAP['env']
    assert order == PathResolution.ENV
"""


def is_path_resolution_literal(value: str) -> TypeGuard[PathResolutionLiteral]:
    """Checks if the given string is a valid PathResolution literal.

    Example
    -------

    .. code-block:: python
        from autopypath.path_resolution import is_path_resolution_literal

        assert is_path_resolution_literal('manual') is True
        assert is_path_resolution_literal('autopypath') is True
        assert is_path_resolution_literal('pyproject') is True
        assert is_path_resolution_literal('invalid') is False

    :param str value: The string to check.
    :return bool: ``True`` if the string is a valid ``PathResolution`` literal, ``False`` otherwise.
    """
    return value in PATH_RESOLUTION_MAP


def resolve_path_resolution_literal(value: str) -> Union[_PathResolution, None]:
    """Resolves a string literal to its corresponding PathResolution enum member
    or returns ``None`` if the literal is invalid.

    Example
    -------

    .. code-block:: python
        from autopypath.path_resolution import resolve_literal, PathResolution

        assert resolve_path_resolution_literal('manual') == PathResolution.MANUAL
        assert resolve_path_resolution_literal('autopypath') == PathResolution.AUTOPYPATH
        assert resolve_path_resolution_literal('pyproject') == PathResolution.PYPROJECT
        assert resolve_path_resolution_literal('invalid') is None

    :param str value: The string literal to resolve.
    :return PathResolution | None: The corresponding PathResolution enum member,
                                    or ``None`` if the literal is invalid.
    """
    if is_path_resolution_literal(value):
        return PATH_RESOLUTION_MAP.get(value)
    return None
