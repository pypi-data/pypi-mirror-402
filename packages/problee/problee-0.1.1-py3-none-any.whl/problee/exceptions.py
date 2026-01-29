"""
Problee SDK Exceptions

Custom exception classes for handling API errors.
"""

from typing import Optional, Dict, Any


class ProbError(Exception):
    """Base exception for all Problee SDK errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(ProbError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401)


class RateLimitError(ProbError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)
        self.retry_after = retry_after


class NotFoundError(ProbError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", resource_type: Optional[str] = None):
        super().__init__(message, code="NOT_FOUND", status_code=404)
        self.resource_type = resource_type


class ValidationError(ProbError):
    """Raised when request validation fails."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400)
        self.errors = errors or []


class APIError(ProbError):
    """Raised for general API errors."""

    pass


class QuoteExpiredError(ProbError):
    """Raised when a quote has expired."""

    def __init__(self, message: str = "Quote has expired"):
        super().__init__(message, code="QUOTE_EXPIRED", status_code=400)


class InsufficientSharesError(ProbError):
    """Raised when user doesn't have enough shares."""

    def __init__(self, message: str = "Insufficient shares"):
        super().__init__(message, code="INSUFFICIENT_SHARES", status_code=400)
