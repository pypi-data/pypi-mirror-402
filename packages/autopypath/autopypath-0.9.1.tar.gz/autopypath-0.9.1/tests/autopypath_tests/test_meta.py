"""Tests for :mod:`autopypath._meta` module."""

from autopypath._meta import (
    __author__,
    __copyright__,
    __license__,
    __project__,
    __release__,
    __url__,
    __version__,
)


def test_meta_attributes() -> None:
    """Test that metadata attributes are correctly defined."""
    assert isinstance(__author__, str), 'Author should be a string'
    assert isinstance(__copyright__, str), 'Copyright should be a string'
    assert isinstance(__license__, str), 'License should be a string'
    assert isinstance(__project__, str), 'Project name should be a string'
    assert isinstance(__release__, str), 'Release should be a string'
    assert isinstance(__url__, str), 'URL should be a string'
    assert isinstance(__version__, str), 'Version should be a string'
