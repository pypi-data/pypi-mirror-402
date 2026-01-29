"""
Custom exceptions for the CryptoHFTData SDK.
"""

from typing import Any, Dict, Optional


class CryptoHFTDataError(Exception):
    """Base exception class for all CryptoHFTData SDK errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class APIError(CryptoHFTDataError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)
        self.status_code = status_code
        self.response_body = response_body


class ValidationError(CryptoHFTDataError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)
        self.field = field
        self.value = value


class AuthenticationError(CryptoHFTDataError):
    """Raised when authentication fails."""

    pass


class RateLimitError(CryptoHFTDataError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)
        self.retry_after = retry_after


class DataNotFoundError(CryptoHFTDataError):
    """Raised when requested data is not found."""

    pass


class ConfigurationError(CryptoHFTDataError):
    """Raised when there's a configuration error."""

    pass


class NetworkError(CryptoHFTDataError):
    """Raised when there's a network-related error."""

    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)
        self.original_exception = original_exception


class TimeoutError(CryptoHFTDataError):
    """Raised when a request times out."""

    pass


class DataFormatError(CryptoHFTDataError):
    """Raised when data format is invalid or unexpected."""

    pass
