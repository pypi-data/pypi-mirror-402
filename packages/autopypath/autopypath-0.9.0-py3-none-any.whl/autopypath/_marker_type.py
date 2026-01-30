"""Marker types for repository markers."""

from enum import Enum
from types import MappingProxyType
from typing import Union

from ._doc_utils import enum_docstrings
from ._typing import Final, Literal, TypeAlias, TypeGuard

__all__ = ['_MarkerType']


@enum_docstrings
class _MarkerType(str, Enum):
    """Types of repository markers used to identify the repository root.

    - FILE: A file that must exist in the repository root.
    - DIR: A directory that must exist in the repository root.

    Example
    -------
    .. code-block:: python
        from autopypath.marker_type import MarkerType

        marker_type = MarkerType.FILE

    """

    FILE = 'file'
    """A file that must exist in the repository root."""
    DIR = 'dir'
    """A directory that must exist in the repository root."""


MarkerTypeLiteral: TypeAlias = Literal['file', 'dir']
"""Literal type for MarkerType values."""


MARKER_TYPE_MAP: Final[MappingProxyType[MarkerTypeLiteral, _MarkerType]] = MappingProxyType(
    {marker.value: marker for marker in _MarkerType}
)
"""Mapping from literal strings to MarkerType enum members.

Example
-------

.. code-block:: python

    from autopypath.marker_type import MARKER_TYPE_MAP, MarkerType

    marker_type = MARKER_TYPE_MAP['file']
    assert marker_type == MarkerType.FILE
"""


def is_marker_type_literal(value: str) -> TypeGuard[MarkerTypeLiteral]:
    """Checks if the given string is a valid MarkerType literal.

    Example
    -------

    .. code-block:: python
        from autopypath.marker_type import is_marker_type_literal

        assert is_marker_type_literal('file') is True
        assert is_marker_type_literal('dir') is True
        assert is_marker_type_literal('invalid') is False

    :param str value: The string to check.
    :return bool: ``True`` if the string is a valid ``MarkerType`` literal, ``False`` otherwise.
    """
    return value in MARKER_TYPE_MAP


def resolve_marker_type_literal(value: str) -> Union[_MarkerType, None]:
    """Resolves a string literal to its corresponding MarkerType enum member
    or returns ``None`` if the literal is invalid.

    Example
    -------

    .. code-block:: python
        from autopypath.path_resolution_order import resolve_marker_type_literal, PathResolution

        assert resolve_marker_type_literal('file') == MarkerType.FILE
        assert resolve_marker_type_literal('dir') == MarkerType.DIR
        assert resolve_marker_type_literal('invalid') is None
    :param str value: The string literal to resolve.
    :return MarkerType | None: The corresponding MarkerType enum member,
                               or ``None`` if the literal is invalid.
    """
    if is_marker_type_literal(value):
        return MARKER_TYPE_MAP.get(value)
    return None
