"""Helper functions to access resources bundled with this package.

These functions provide a high-level API to read text or binary files from
within the installed ``bundled_assets`` package.  They rely on the
``importlib.resources`` module, which correctly handles files inside zip
archives (such as wheel distributions) without assuming that the data lives
on the filesystem.  See the Python documentation for more details:
https://docs.python.org/3/library/importlib.resources.html
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator


def _resource_path(rel_path: str) -> resources.abc.Traversable:
    """Return a Traversable pointing to a resource under ``data``.

    Parameters
    ----------
    rel_path: str
        The relative path under the ``data`` directory.  For example
        ``"templates/prompt.txt"``.

    Returns
    -------
    resources.abc.Traversable
        An object representing the resource.  This can be passed to
        :func:`importlib.resources.as_file` to obtain a real filesystem path.
    """
    base = resources.files(__package__).joinpath("data")
    return base.joinpath(rel_path)


def read_text(rel_path: str, encoding: str = "utf-8") -> str:
    """Read a text resource bundled with the package.

    This function reads a file located in the ``data`` directory of
    ``bundled_assets`` and returns its contents as a string.

    Parameters
    ----------
    rel_path: str
        The relative path to the file inside the ``data`` directory.

    encoding: str, optional
        The text encoding to use.  Defaults to ``"utf-8"``.

    Returns
    -------
    str
        The decoded text contents of the file.
    """
    resource = _resource_path(rel_path)
    return resource.read_text(encoding=encoding)


def read_bytes(rel_path: str) -> bytes:
    """Read a binary resource bundled with the package.

    Parameters
    ----------
    rel_path: str
        The relative path to the file inside the ``data`` directory.

    Returns
    -------
    bytes
        The raw bytes of the resource.
    """
    resource = _resource_path(rel_path)
    return resource.read_bytes()


@contextmanager
def as_file_path(rel_path: str) -> Iterator[Path]:
    """Yield a real filesystem path to a bundled resource.

    Some libraries require a path on disk rather than a file-like object.
    This context manager yields a :class:`~pathlib.Path` pointing to a
    temporary copy of the resource if the package is installed as a zip
    archive.  When the context exits, any temporary files are cleaned up.

    Example
    -------
    >>> from bundled_assets.assets import as_file_path
    >>> with as_file_path("templates/prompt.txt") as path:
    ...     print(path.read_text())

    Parameters
    ----------
    rel_path: str
        The relative path to the file inside the ``data`` directory.

    Yields
    ------
    pathlib.Path
        A path object pointing to the resource.
    """
    resource = _resource_path(rel_path)
    # resources.as_file returns a context manager that yields a real Path
    with resources.as_file(resource) as tmp_path:
        yield tmp_path