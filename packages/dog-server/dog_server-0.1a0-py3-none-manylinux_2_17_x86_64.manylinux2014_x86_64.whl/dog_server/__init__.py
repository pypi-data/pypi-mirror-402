"""Dog CLI - Python wrapper for the Dog binary."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("dog-server")
except PackageNotFoundError:
    __version__ = "0.1a0-dev"  # Fallback for development
