"""Configuration modules for autopypath.

This module contains various configuration classes for autopypath,
each designed to load configuration settings from different sources.

The available configuration classes include:

- :class:`Config`: Base configuration class.
- :class:`TomlConfig`: Base class for TOML-based configurations.
- :class:`AutopypathConfig`: Configuration from autopypath.toml files.
- :class:`DefaultConfig`: Default configuration.
- :class:`ManualConfig`: Configuration from manual paths.
- :class:`PyProjectConfig`: Configuration from pyproject.toml files.
"""
# ruff: noqa F401

from ._autopypath import _AutopypathConfig
from ._config import _Config
from ._default import _DefaultConfig
from ._manual import _ManualConfig
from ._pyproject import _PyProjectConfig
from ._toml import _TomlConfig

__all__ = []
