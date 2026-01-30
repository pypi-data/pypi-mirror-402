"""Types for autopypath.

This module exposes special types used by autopypath.
"""

from .._typing import Literal, TypeAlias
from ._no_path import _NoPath  # noqa: F401

RepoMarkerLiterals: TypeAlias = Literal['dir', 'file']
"""Type alias for repository marker literals."""

LoadStrategyLiterals: TypeAlias = Literal['prepend', 'prepend_highest_priority', 'replace']
"""Type alias for load strategy literals."""

PathResolutionLiterals: TypeAlias = Literal['manual', 'autopypath', 'pyproject']
"""Type alias for path resolution order literals."""

__all__ = ['RepoMarkerLiterals', 'LoadStrategyLiterals', 'PathResolutionLiterals']
