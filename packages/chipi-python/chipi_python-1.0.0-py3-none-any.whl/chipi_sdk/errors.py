"""Error classes and utilities for Chipi SDK."""

from typing import Any, Optional


class ChipiError(Exception):
    """Base exception for Chipi SDK."""

    def __init__(
        self, message: str, code: str = "UNKNOWN_ERROR", status: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class ChipiApiError(ChipiError):
    """API request errors."""

    def __init__(self, message: str, code: str, status: int):
        super().__init__(message, code, status)


class ChipiWalletError(ChipiError):
    """Wallet operation errors."""

    def __init__(self, message: str, code: str = "WALLET_ERROR"):
        super().__init__(message, code)


class ChipiTransactionError(ChipiError):
    """Transaction execution errors."""

    def __init__(self, message: str, code: str = "TRANSACTION_ERROR"):
        super().__init__(message, code)


class ChipiSessionError(ChipiError):
    """Session management errors."""

    def __init__(self, message: str, code: str = "SESSION_ERROR"):
        super().__init__(message, code)


class ChipiSkuError(ChipiError):
    """SKU-related errors."""

    def __init__(self, message: str, code: str = "SKU_ERROR"):
        super().__init__(message, code)


class ChipiValidationError(ChipiError):
    """Validation errors."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, 400)


class ChipiAuthError(ChipiError):
    """Authentication errors."""

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code, 401)


def is_chipi_error(error: Any) -> bool:
    """Check if an error is a ChipiError instance."""
    return isinstance(error, ChipiError)


def handle_api_error(error: Any) -> ChipiError:
    """
    Convert various error types to ChipiError.

    Args:
        error: Any exception or error object

    Returns:
        ChipiError instance
    """
    if is_chipi_error(error):
        return error

    # Handle httpx or requests errors
    if hasattr(error, "response"):
        status = getattr(error.response, "status_code", None)
        if status:
            try:
                data = error.response.json()
                message = data.get("message", str(error))
                code = data.get("code", f"HTTP_{status}")
            except Exception:
                message = str(error)
                code = f"HTTP_{status}"
            return ChipiApiError(message, code, status)

    # Default case
    message = str(error) if error else "An unknown error occurred"
    return ChipiError(message, "UNKNOWN_ERROR")
