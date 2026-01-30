"""Janet AI CLI - Sync tickets to local markdown files."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("janet-cli")
except PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for local development
