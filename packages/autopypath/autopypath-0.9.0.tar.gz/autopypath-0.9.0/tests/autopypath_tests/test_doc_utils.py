import ast
from enum import Enum
from unittest.mock import patch

from autopypath._doc_utils import enum_docstrings


@enum_docstrings
class Color(Enum):
    """Enumeration of colors."""

    RED = 1
    """The color red."""

    GREEN = 2
    """The color green."""

    BLUE = 3
    """The color blue."""


def test_enum_docstrings() -> None:
    assert Color.__doc__ == 'Enumeration of colors.'
    assert Color.RED.__doc__ == 'The color red.'
    assert Color.GREEN.__doc__ == 'The color green.'
    assert Color.BLUE.__doc__ == 'The color blue.'


def test_not_an_enum() -> None:
    class NotAnEnum:
        pass

    try:
        enum_docstrings(NotAnEnum)  # type: ignore
    except TypeError as e:
        assert str(e) == 'enum_docstrings can only be applied to Enum subclasses.'
    else:
        raise AssertionError('TypeError was not raised for non-enum class')


def test_enum_docstrings_oserror() -> None:
    class WierdEnum(Enum):
        pass

    with patch('inspect.getsource', side_effect=OSError):
        result = enum_docstrings(WierdEnum)
        assert result is WierdEnum


def test_enum_docstrings_no_classdef() -> None:
    class DummyEnum(Enum):
        X = 1

    # Patch ast.parse to return a module with a non-classdef as the first body element
    fake_mod = ast.Module(body=[ast.Expr(value=ast.Constant(value=42))], type_ignores=[])
    with patch('ast.parse', return_value=fake_mod):
        result = enum_docstrings(DummyEnum)
        assert result is DummyEnum


def test_enum_docstrings_no_docstring() -> None:
    class DocEnum(Enum):
        A = 1
        """docstring for A"""
        B = 2
        """docstring for B"""

    result = enum_docstrings(DocEnum)
    assert result is DocEnum, f'Expected DocEnum, got {result!r}'
    assert DocEnum.A.__doc__ == 'docstring for A', f'Expected docstring for A, got {DocEnum.A.__doc__!r}'
    assert DocEnum.B.__doc__ == 'docstring for B', f'Expected docstring for B, got {DocEnum.B.__doc__!r}'


def test_enum_docstrings_unassigned_docstring() -> None:
    class UnassignedEnum(Enum):
        """An enum with unassigned docstrings"""

        X = 1
        """Unassigned docstring for X"""

        Y = 2
        """Unassigned docstring for Y"""

    unassigned = 'An enum with unassigned docstrings'
    result = UnassignedEnum
    assert result is UnassignedEnum
    assert UnassignedEnum.X.__doc__ == unassigned, f'Expected {unassigned!r}, got {UnassignedEnum.X.__doc__!r}'
    assert UnassignedEnum.Y.__doc__ == unassigned, f'Expected {unassigned!r}, got {UnassignedEnum.Y.__doc__!r}'


def test_enum_docstrings_mixed() -> None:
    @enum_docstrings
    class MixedEnum(Enum):
        """An enum with mixed docstrings"""

        A = 1
        """Docstring for A"""

        B = 2
        # No docstring for B

        C = 3
        """Docstring for C"""

    unassigned = 'An enum with mixed docstrings'

    result = MixedEnum
    assert result is MixedEnum
    assert MixedEnum.A.__doc__ == 'Docstring for A', f'Expected docstring for A, got {MixedEnum.A.__doc__!r}'
    assert MixedEnum.B.__doc__ == unassigned, f'Expected {unassigned!r}, got {MixedEnum.B.__doc__!r}'
    assert MixedEnum.C.__doc__ == 'Docstring for C', f'Expected docstring for C, got {MixedEnum.C.__doc__!r}'


class DummyEnum(Enum):
    A = 1


def test_enum_docstrings_invalid_ast() -> None:
    """Test enum_docstrings when AST does not contain a ClassDef."""
    # Patch inspect.getsource to return a function definition instead of a class
    fake_source = 'def not_a_class():\n    pass\n'
    with patch('inspect.getsource', return_value=fake_source):
        result = enum_docstrings(DummyEnum)
        assert result is DummyEnum  # Should return the enum unchanged
