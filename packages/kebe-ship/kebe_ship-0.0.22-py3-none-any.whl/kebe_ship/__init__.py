"""Utilities for accessing bundled data files.

This package bundles configuration files, templates and binary resources in
``bundled_assets/data``.  Use the functions from :mod:`bundled_assets.assets`
to read these resources as text or bytes.
"""

from .assets import read_text, read_bytes, as_file_path

__all__ = ["read_text", "read_bytes", "as_file_path"]