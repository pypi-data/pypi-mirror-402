"""Decorators for enums."""

import ast
import inspect
import textwrap
from enum import Enum
from functools import partial
from operator import is_
from typing import TypeVar, Union

E = TypeVar('E', bound=Enum)


# Decorator to attach docstrings to enum members
# See: https://stackoverflow.com/questions/19330460/how-do-i-put-docstrings-on-enums
def enum_docstrings(enum: type[E]) -> type[E]:
    """Attach docstrings to enum members.

    Docstrings are string literals that appear directly below the enum member
    assignment expression within triple-quotes.

    This decorator parses the source code of the enum class to find
    docstrings for each member and attaches them to the respective enum members.

    This allows for more detailed documentation of enum members and in tools
    that can extract and display these docstrings.

    This code is adapted from:
    https://stackoverflow.com/questions/19330460/how-do-i-put-docstrings-on-enums

    .. code-block:: python
      :caption: Example usage of enum_docstrings decorator
      :linenos:

      @enum_docstrings
      class SomeEnum(Enum):
          '''Docstring for the SomeEnum enum'''

          foo_member = 'foo_value'
          '''Docstring for the foo_member enum member'''


      SomeEnum.foo_member.__doc__  # 'Docstring for the foo_member enum member'

    :param enum: The enum class to process.
    :return: The same enum class with member docstrings attached.
    """
    if not issubclass(enum, Enum):
        raise TypeError('enum_docstrings can only be applied to Enum subclasses.')

    try:
        source = inspect.getsource(enum)
        source = textwrap.dedent(source)
        mod = ast.parse(source)
    except OSError:  # Fallback case where source code is not available
        return enum

    # with the source parsed, find the class definition
    # if there is no class definition, return the enum unmodified
    if not (mod.body and isinstance(class_def := mod.body[0], ast.ClassDef)):
        return enum

    # An enum member docstring is unassigned if it is the exact same object
    # as enum.__doc__.
    unassigned = partial(is_, enum.__doc__)
    names = enum.__members__.keys()
    member: Union[E, None] = None
    for node in class_def.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and (name := node.targets[0].id) in names
        ):
            # Enum member assignment, look for a docstring next
            member = enum[name]
            continue

        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and member
            and unassigned(member.__doc__)
        ):
            # docstring immediately following a member assignment
            member.__doc__ = node.value.value

        else:
            pass

        member = None

    return enum
