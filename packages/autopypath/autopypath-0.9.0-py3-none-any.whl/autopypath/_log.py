"""Logging setup for autopypath package."""

import logging

__all__ = []



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_log = logging.getLogger('autopypath')
"""Logging instance for the autopypath package."""
