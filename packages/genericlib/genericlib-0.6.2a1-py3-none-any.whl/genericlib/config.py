"""
genericlib.config
=================

Package metadata and configuration attributes.

This module centralizes versioning information for the `genericlib` package,
providing a single source of truth for the current release version. By exposing
the `version` attribute, it ensures consistency across the package when reporting,
logging, or displaying edition details.
"""

__version__ = '0.6.2a1'
version = __version__

__all__ = [
    'version'
]
