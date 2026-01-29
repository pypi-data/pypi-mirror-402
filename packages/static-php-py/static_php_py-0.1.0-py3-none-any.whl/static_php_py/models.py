"""Data models for PHP execution results."""


class ExecutionResult:
    """Represent PHP script execution outcome.

    Contains execution status, exit code, and captured output streams.
    Success is determined by zero exit code.

    Attributes:
        success: True if script completed with exit code 0.
        return_code: Process exit code from subprocess.
        stdout: Standard output content as string.
        stderr: Standard error content as string.
    """

    def __init__(
        self,
        return_code: int,
        stdout: str,
        stderr: str,
    ) -> None:
        """Initialize execution result.

        Args:
            return_code: Process exit code.
            stdout: Standard output content.
            stderr: Standard error content.
        """
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.success = return_code == 0

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        status = "success" if self.success else f"failed (code {self.return_code})"
        return (
            f"ExecutionResult({status}, "
            f"stdout={len(self.stdout)} chars, "
            f"stderr={len(self.stderr)} chars)"
        )
