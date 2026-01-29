"""PHP binary wrapper for script execution."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from platformdirs import user_cache_dir

from static_php_py.exceptions import BinaryNotFoundError, ExecutionError
from static_php_py.models import ExecutionResult
from static_php_py.providers import (
    _PathProvider,
    _RemoteProvider,
    _ResourceProvider,
)

logger = logging.getLogger(__name__)


class PHP:
    """Represent a PHP binary and execute PHP scripts.

    Wraps a PHP executable and provides methods for script execution,
    code evaluation, and version queries.

    Attributes:
        _binary_path: Path to PHP executable.
    """

    def __init__(self, binary_path: Path) -> None:
        """Initialize PHP instance with binary path.

        Args:
            binary_path: Path to PHP executable.
        """
        self._binary_path = binary_path

    @staticmethod
    def builtin() -> PHP:
        """Load built-in PHP binary from package resources.

        Uses the PHP binary bundled in platform-specific wheels.
        The binary is automatically extracted on first use.

        Returns:
            PHP instance wrapping the built-in binary.

        Raises:
            BinaryNotFoundError: If built-in binary not found (not installed 
                via platform-specific wheel).
        """
        provider = _ResourceProvider()
        binary_path = provider.resolve()
        return PHP(binary_path)

    @staticmethod
    def local(path: Path | str) -> PHP:
        """Load PHP binary from local file system path.

        Args:
            path: Path to PHP binary (required, cannot be None).

        Returns:
            PHP instance wrapping the local binary.

        Raises:
            BinaryNotFoundError: If binary not found at specified path.
        """
        if path is None:
            raise BinaryNotFoundError("Path argument is required for local()")
        
        provider = _PathProvider(path)
        binary_path = provider.resolve()
        return PHP(binary_path)

    @staticmethod
    def remote(url: str, force: bool = False, timeout: float = 300.0) -> PHP:
        """Download PHP binary from remote URL and return PHP instance.

        Downloads PHP binary or archive (tar.gz, tgz, or zip) from remote URL,
        extracts if needed, sets execute permission, caches locally, and returns
        a PHP instance.

        Args:
            url: Remote URL to PHP binary or archive (tar.gz, tgz, or zip).
            force: Force re-download ignoring cache (default: False).
            timeout: Download timeout in seconds (default: 300.0).

        Returns:
            PHP instance wrapping the downloaded binary.

        Raises:
            DownloadError: If network/HTTP error occurs.
            InvalidArchiveError: If archive format invalid or no php executable found.
        """
        provider = _RemoteProvider(url, force=force, timeout=timeout)
        binary_path = provider.resolve()
        return PHP(binary_path)

    def run(
        self,
        script: Path | str,
        args: list[str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """Execute PHP script file.

        Args:
            script: Path to PHP script file.
            args: Optional arguments passed to script.
            timeout: Optional timeout in seconds.

        Returns:
            ExecutionResult with execution outcome.

        Raises:
            FileNotFoundError: If script file does not exist.
            ExecutionError: If subprocess execution fails unexpectedly.
        """
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"PHP script not found: {script_path}")

        cmd = [str(self._binary_path), str(script_path)]
        if args:
            cmd.extend(args)

        return self._execute(cmd, timeout)

    def eval(self, code: str, timeout: float | None = None) -> ExecutionResult:
        """Execute PHP code string via php -r.

        Args:
            code: PHP code to execute.
            timeout: Optional timeout in seconds.

        Returns:
            ExecutionResult with execution outcome.

        Raises:
            ExecutionError: If subprocess execution fails unexpectedly.
        """
        cmd = [str(self._binary_path), "-r", code]
        return self._execute(cmd, timeout)

    def version(self) -> str:
        """Get PHP version string.

        Supports both standard PHP and static-php-cli version formats:
        - Standard PHP: "PHP 8.3.0 (cli) ..."
        - static-php-cli: "static-php-cli 2.7.10"

        Returns:
            Version string (e.g., "8.3.0" or "2.7.10").

        Raises:
            ExecutionError: If version query fails.
        """
        result = self._execute([str(self._binary_path), "--version"], timeout=5.0)
        if not result.success:
            logger.error("Failed to get PHP version: %s", result.stderr)
            raise ExecutionError(f"Failed to get PHP version: {result.stderr}")

        # Try standard PHP format first: "PHP 8.3.0"
        match = re.search(r"PHP\s+(\d+\.\d+\.\d+)", result.stdout, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try static-php-cli format: "static-php-cli 2.7.10"
        match = re.search(r"static-php-cli\s+(\d+\.\d+\.\d+)", result.stdout, re.IGNORECASE)
        if match:
            return f"static-php-cli {match.group(1)}"

        logger.error("Cannot parse version from output: %s", result.stdout)
        raise ExecutionError(f"Cannot parse version from: {result.stdout}")

    def path(self) -> Path:
        """Get PHP binary path.

        Returns:
            Path to PHP executable.
        """
        return self._binary_path

    @staticmethod
    def cache_dir() -> Path:
        """Get cache directory path where binaries are stored.

        Returns the platform-specific user cache directory where PHP binaries
        from package resources or remote downloads are cached. This directory
        is persistent and typically not cleaned by system cleanup tools.

        Platform-specific locations:
        - Linux: ~/.cache/static-php-py/
        - macOS: ~/Library/Caches/static-php-py/
        - Windows: C:\\Users\\<user>\\AppData\\Local\\static-php-py\\

        Returns:
            Path to cache directory.
        """
        return Path(user_cache_dir("static-php-py", "static-php-py"))

    def _execute(self, cmd: list[str], timeout: float | None) -> ExecutionResult:
        """Execute subprocess and capture output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return ExecutionResult(
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired as e:
            logger.error("PHP execution timeout after %.2f seconds", timeout or 0)
            raise ExecutionError(f"PHP execution timeout after {timeout}s") from e
        except OSError as e:
            logger.exception("Failed to execute PHP binary: %s", self._binary_path)
            raise ExecutionError(f"Failed to execute PHP binary {self._binary_path}: {e}") from e
