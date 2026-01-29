"""Python wrapper library for static PHP binaries.

This library provides a Python interface for PHP script execution with pre-built
static PHP binaries distributed via platform-specific wheels.

Inspired by crazywhalecc/static-php-cli project.
"""

from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import re


def _read_version_from_pyproject() -> str:
    """Read version from pyproject.toml (development fallback)."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
    return "0.0.0.dev"


try:
    __version__ = version("static-php-py")
except PackageNotFoundError:
    # Package not installed (e.g., during development) - read from pyproject.toml
    __version__ = _read_version_from_pyproject()

from static_php_py.exceptions import (
    BinaryNotFoundError,
    DownloadError,
    ExecutionError,
    InvalidArchiveError,
    PHPError,
)
from static_php_py.models import ExecutionResult
from static_php_py.php import PHP

__all__ = [
    "PHPError",
    "BinaryNotFoundError",
    "ExecutionError",
    "DownloadError",
    "InvalidArchiveError",
    "ExecutionResult",
    "PHP",
]
