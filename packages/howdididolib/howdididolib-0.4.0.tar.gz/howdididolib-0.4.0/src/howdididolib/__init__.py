"""A Python library for retrieving golf booking and fixture information from How Did I Do."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("howdididolib")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0"
