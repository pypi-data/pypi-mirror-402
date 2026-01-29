"""PHP binary providers for different resolution strategies."""

from __future__ import annotations

import hashlib
import importlib.resources
import logging
import os
import platform
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Protocol

from platformdirs import user_cache_dir

from static_php_py.exceptions import BinaryNotFoundError, DownloadError, InvalidArchiveError

logger = logging.getLogger(__name__)


class _PHPProvider(Protocol):
    """Protocol defining interface for PHP binary resolution strategies.

    All provider implementations must implement the resolve() method
    to return a valid PHP executable path or raise BinaryNotFoundError.
    """

    def resolve(self) -> Path:
        """Resolve and return PHP binary path.

        Returns:
            Path to PHP executable.

        Raises:
            BinaryNotFoundError: If resolution fails.
        """
        ...


class _PathProvider:
    """Resolve PHP binary from explicit path or system PATH.

    Implements two-tier resolution:
    1. If explicit path provided, validate and return it
    2. Otherwise, search system PATH for php executable

    Attributes:
        _explicit_path: User-specified path to PHP binary, or None.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        """Initialize with optional explicit path.

        Args:
            path: Optional explicit path to PHP binary.
        """
        self._explicit_path = Path(path) if path else None

    def resolve(self) -> Path:
        """Return explicit path if provided, otherwise search system PATH.

        Returns:
            Path to PHP executable.

        Raises:
            BinaryNotFoundError: If PHP binary not found.
        """
        if self._explicit_path:
            if not self._validate_binary(self._explicit_path):
                raise BinaryNotFoundError(
                    f"PHP binary not found at explicit path: {self._explicit_path}"
                )
            return self._explicit_path

        path = self._find_in_path()
        if not path:
            raise BinaryNotFoundError(
                "PHP binary not found in system PATH. "
                "Install PHP or use create(path=...) to specify location."
            )

        return path

    def _find_in_path(self) -> Path | None:
        """Search system PATH for php executable."""
        php_path = shutil.which("php")
        if not php_path:
            logger.debug("PHP not found in system PATH")
            return None

        resolved = Path(php_path)
        logger.debug("Found PHP in PATH: %s", resolved)
        return resolved

    def _validate_binary(self, path: Path) -> bool:
        """Check if path exists and is executable."""
        if not path.exists():
            logger.debug("Path does not exist: %s", path)
            return False

        if not path.is_file():
            logger.debug("Path is not a file: %s", path)
            return False

        if not os.access(path, os.X_OK):
            logger.debug("Path is not executable: %s", path)
            return False

        return True


class _ResourceProvider:
    """Load PHP binary from package resources.

    Loads pre-built PHP binary from resources directory.
    The binary should already exist in the package (extracted during wheel
    installation). No runtime extraction or platform detection.

    Attributes:
        _package_dir: Directory where package is installed.
    """

    def __init__(self) -> None:
        """Initialize resource provider."""
        self._package_dir = self._get_package_directory()

    def _get_package_directory(self) -> Path:
        """Get package installation directory."""
        try:
            package = importlib.resources.files("resources")
            # importlib.resources.files() returns a Path-like object
            if isinstance(package, Path):
                # If it's a file, get parent; if directory, use directly
                if package.is_file():
                    return package.parent
                return package
            # Fallback: try to convert to Path
            return Path(str(package))
        except (ModuleNotFoundError, AttributeError, TypeError) as e:
            logger.error("Cannot determine package directory: %s", e)
            raise BinaryNotFoundError(
                "PHP binary not found in package resources. "
                "Install platform-specific wheel or use create(path=...) to specify location."
            ) from e

    def resolve(self) -> Path:
        """Load PHP binary from package resources.

        Simply checks if php binary exists in resources directory.

        Returns:
            Path to PHP executable in resources directory.

        Raises:
            BinaryNotFoundError: If binary not found.
        """
        # Check for php binary in package directory
        package_binary = self._package_dir / "php"
        
        if not package_binary.exists():
            logger.error("PHP binary not found in resources directory: %s", package_binary)
            raise BinaryNotFoundError(
                f"PHP binary not found at {package_binary}. "
                "Install platform-specific wheel or use PHP.local(path) to specify location."
            )

        # If binary exists but not executable, set permission
        if not os.access(package_binary, os.X_OK):
            try:
                os.chmod(package_binary, 0o755)
                logger.debug("Set execute permission on binary: %s", package_binary)
            except OSError as e:
                logger.warning("Cannot set execute permission: %s", e)

        logger.debug("Using binary from resources: %s", package_binary)
        return package_binary



class _RemoteProvider:
    """Download and resolve PHP binary from remote URL.

    Downloads PHP binaries or archives (tar.gz, tgz, zip) from remote URLs,
    extracts if needed, and caches them locally. Supports force re-download option.

    Attributes:
        _url: Remote URL to download from.
        _force: Force re-download flag, ignoring cache.
        _timeout: Download timeout in seconds.
        _cache_dir: Directory for downloaded files.
    """

    def __init__(self, url: str, force: bool = False, timeout: float = 300.0) -> None:
        """Initialize remote provider with URL and options.

        Args:
            url: Remote URL to PHP binary or archive (tar.gz, tgz, or zip).
            force: Force re-download ignoring cache.
            timeout: Download timeout in seconds.
        """
        self._url = url
        self._force = force
        self._timeout = timeout

        cache_base = user_cache_dir("static-php-py", "static-php-py")
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        self._cache_dir = Path(cache_base) / "downloads" / url_hash
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self) -> Path:
        """Download file, extract if archive, and return PHP binary path.

        Returns:
            Path to downloaded/extracted PHP executable.

        Raises:
            DownloadError: If network/HTTP download fails.
            InvalidArchiveError: If archive is invalid or missing php executable.
        """
        downloaded_file = self._cache_dir / "downloaded"
        php_binary = self._cache_dir / "php"

        if not self._force and php_binary.exists() and os.access(php_binary, os.X_OK):
            logger.debug("Using cached binary from URL: %s", self._url)
            return php_binary

        if not downloaded_file.exists() or self._force:
            try:
                self._download_file(downloaded_file)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                logger.error("Failed to download from URL: %s", self._url)
                raise DownloadError(f"Failed to download from {self._url}: {e}") from e

        if self._is_archive_url(self._url):
            try:
                extracted_php = self._extract_archive(downloaded_file)
                if extracted_php != php_binary:
                    shutil.copy2(extracted_php, php_binary)
                    os.chmod(php_binary, 0o755)
            except (tarfile.TarError, zipfile.BadZipFile, FileNotFoundError, ValueError) as e:
                logger.error("Failed to extract archive: %s", downloaded_file)
                raise InvalidArchiveError(
                    f"Failed to extract archive or find php executable: {e}"
                ) from e
        else:
            shutil.copy2(downloaded_file, php_binary)
            os.chmod(php_binary, 0o755)

        return php_binary

    def _download_file(self, target_path: Path) -> None:
        """Download file using urllib.request to cache directory."""
        logger.debug("Downloading from URL: %s", self._url)

        try:
            with urllib.request.urlopen(self._url, timeout=self._timeout) as response:
                target_path.write_bytes(response.read())
            logger.debug("Downloaded to: %s", target_path)
        except urllib.error.HTTPError as e:
            raise DownloadError(f"HTTP error {e.code} from {self._url}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise DownloadError(f"URL error from {self._url}: {e.reason}") from e
        except OSError as e:
            raise DownloadError(f"IO error downloading from {self._url}: {e}") from e

    def _is_archive_url(self, url: str) -> bool:
        """Check if URL points to archive by extension.
        
        Supported formats: tar.gz, tgz, zip
        """
        url_lower = url.lower()
        return (url_lower.endswith(".tar.gz") or 
                url_lower.endswith(".tgz") or 
                url_lower.endswith(".zip"))

    def _extract_archive(self, archive_path: Path) -> Path:
        """Extract archive (tar.gz or zip) and locate php executable.

        Args:
            archive_path: Path to downloaded archive file.

        Returns:
            Path to php executable in extracted directory.

        Raises:
            InvalidArchiveError: If extraction fails or php not found.
        """
        extract_dir = self._cache_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)

        # Determine archive type from URL (not filename, since downloaded file is named "downloaded")
        url_lower = self._url.lower()
        try:
            if url_lower.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
            elif url_lower.endswith((".tar.gz", ".tgz")):
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(extract_dir)
            else:
                raise InvalidArchiveError(f"Unsupported archive format: {self._url}")
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            raise InvalidArchiveError(f"Failed to extract archive: {e}") from e

        php_path = self._find_php_in_directory(extract_dir)
        if not php_path:
            raise InvalidArchiveError("No php executable found in extracted archive")

        return php_path

    def _find_php_in_directory(self, directory: Path) -> Path | None:
        """Locate php executable in directory tree.
        
        Searches for executables with common PHP-related names:
        - php, php* (e.g., php8.3, php-cli)
        - spc, spc* (static-php-cli binaries)
        """
        for root, _dirs, files in os.walk(directory):
            for name in files:
                # Check for php, php*, spc, spc* executables
                if name == "php" or name.startswith("php") or name == "spc" or name.startswith("spc"):
                    candidate = Path(root) / name
                    if os.access(candidate, os.X_OK) or candidate.is_file():
                        logger.debug("Found PHP executable: %s", candidate)
                        return candidate

        return None


class _PHPResolver:
    """Internal factory implementing fallback resolution strategy.

    Resolves PHP binary using a priority chain:
    1. Explicit path (if provided) via _PathProvider
    2. Package resource (bundled binary) via _ResourceProvider
    3. System PATH via _PathProvider

    Attributes:
        _path_provider: Provider for explicit path or system PATH resolution.
        _resource_provider: Provider for package resource resolution.
    """

    def __init__(self) -> None:
        """Initialize resolver with provider instances."""
        self._path_provider = _PathProvider()
        self._resource_provider = _ResourceProvider()

    def resolve(self, path: Path | str | None = None) -> Path:
        """Resolve PHP binary using fallback strategy.

        Priority order:
        1. Explicit path (if provided)
        2. Package resource (bundled binary)
        3. System PATH

        Args:
            path: Optional explicit path to PHP binary.

        Returns:
            Path to PHP executable.

        Raises:
            BinaryNotFoundError: If all resolution methods fail.
        """
        # Priority 1: If explicit path provided, use it
        if path:
            path_provider = _PathProvider(path)
            try:
                resolved = path_provider.resolve()
                logger.debug("Resolved PHP binary via explicit path: %s", resolved)
                return resolved
            except BinaryNotFoundError as e:
                logger.error("Explicit path failed: %s", path)
                raise BinaryNotFoundError(
                    f"PHP binary not found at explicit path: {path}"
                ) from e

        # Priority 2: Try package resource (bundled binary)
        try:
            resolved = self._resource_provider.resolve()
            logger.debug("Resolved PHP binary via ResourceProvider: %s", resolved)
            return resolved
        except BinaryNotFoundError:
            logger.debug("ResourceProvider failed, trying system PATH")

        # Priority 3: Fall back to system PATH
        path_provider = _PathProvider(None)
        try:
            resolved = path_provider.resolve()
            logger.debug("Resolved PHP binary via system PATH: %s", resolved)
            return resolved
        except BinaryNotFoundError as e:
            logger.error("All resolution methods failed")
            raise BinaryNotFoundError(
                "PHP binary not found. "
                "Install PHP system-wide, use create(path=...) to specify location, "
                "or install platform-specific wheel with bundled binary."
            ) from e
