from __future__ import annotations

"""Exception classes for the Amp Python SDK."""

import asyncio

# ============================================================================
# Base Exception Classes
# ============================================================================


class AmpError(Exception):
    """Base exception class for all Amp SDK errors."""

    def __init__(self, message: str, exit_code: int = 1, details: str = "") -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details


class CLINotFoundError(AmpError):
    """Raised when the Amp CLI cannot be found."""

    def __init__(self, message: str = "Amp CLI not found") -> None:
        super().__init__(
            message,
            exit_code=127,
            details="Please install the Amp CLI: npm install -g @sourcegraph/amp",
        )


# ============================================================================
# CLI and Process Errors
# ============================================================================


class ProcessError(AmpError):
    """Raised when the Amp CLI process fails."""

    def __init__(self, message: str, exit_code: int, stderr: str = "", signal: str = "") -> None:
        super().__init__(message, exit_code=exit_code, details=stderr)
        self.stderr = stderr
        self.signal = signal


# ============================================================================
# Data and Validation Errors
# ============================================================================


class ValidationError(AmpError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "") -> None:
        super().__init__(message, exit_code=1)
        self.field = field


class JSONParseError(AmpError):
    """Raised when JSON parsing fails."""

    def __init__(self, message: str, raw_line: str = "") -> None:
        super().__init__(message, exit_code=1)
        self.raw_line = raw_line


# ============================================================================
# Execution Control Errors
# ============================================================================


class AmpTimeoutError(AmpError):
    """Raised when an operation times out."""

    def __init__(self, message: str = "Operation timed out") -> None:
        super().__init__(message, exit_code=124)


class CancellationError(asyncio.CancelledError, AmpError):
    """Raised when an operation is cancelled."""

    def __init__(self, message: str = "Operation was cancelled") -> None:
        AmpError.__init__(self, message, exit_code=130)
