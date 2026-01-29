"""Exception classes for static-php-py.

All exceptions inherit from PHPError base class for easy catching.
"""


class PHPError(Exception):
    """Base exception for all static-php-py errors.

    All library-specific exceptions inherit from this class, allowing
    consumers to catch all library errors with a single except clause.
    """


class BinaryNotFoundError(PHPError):
    """PHP binary cannot be found through any resolution method.

    Raised when:
    - Explicit path does not exist or is not executable
    - No php executable found in system PATH
    - Package resource binary not available (basic extra not installed)

    Args:
        message: Description of where binary resolution failed.
    """


class ExecutionError(PHPError):
    """PHP subprocess execution failed unexpectedly.

    Raised when subprocess fails to start or encounters system-level errors,
    not for PHP script errors (which return ExecutionResult with non-zero exit code).

    Args:
        message: Description of execution failure.
    """


class DownloadError(PHPError):
    """Remote download failed due to network or HTTP error.

    Raised when:
    - Network connection fails
    - HTTP request returns error status code
    - Download timeout exceeded
    - URL protocol not supported (only http/https allowed)

    Args:
        message: Description of download failure including URL.
    """


class InvalidArchiveError(PHPError):
    """Archive is corrupted or does not contain php executable.

    Raised when:
    - tar.gz extraction fails (corrupt archive)
    - Extracted archive does not contain any php executable
    - Archive format is not supported

    Args:
        message: Description of archive validation failure.
    """
