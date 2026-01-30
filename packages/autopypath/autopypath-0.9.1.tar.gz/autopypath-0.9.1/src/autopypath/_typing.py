"""Special types used in AutoPyPath.

This module provides compatibility imports for typing features
across different Python versions that may not have them natively.

The types provided here include:
- :class:`Literal`
- :class:`Final`
- :class:`Never`
- :class:`TypeAlias`
- :class:`TypeGuard`

"""
# ruff: noqa: F401

__all__ = []

# Compatibility imports for typing features
# This is a 'feature detection' pattern to support multiple Python versions
# without having to know exactly which versions support which features.
try:
    from typing import Literal  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # Will only occur on very old Python versions
    from typing_extensions import Literal

try:
    from typing import Final  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # Will only occur on very old Python versions
    from typing_extensions import Final

try:
    from typing import TypeAlias  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # Will only occur on very old Python versions
    from typing_extensions import TypeAlias

try:
    from typing import TypeGuard  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # Will only occur on very old Python versions
    from typing_extensions import TypeGuard

try:
    from typing import Never  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # Will only occur on very old Python versions
    from typing_extensions import Never
