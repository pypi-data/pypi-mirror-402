"""
Jasni SDK Error Classes

Custom exceptions for handling API errors with specific error types
for different HTTP status codes.
"""

from typing import Optional


class JasniError(Exception):
    """
    Base error class for all Jasni SDK errors.
    
    Attributes:
        message: Human-readable error message
        status: HTTP status code
        code: Error code or type
    """
    
    def __init__(
        self,
        message: str,
        status: int = 0,
        code: str = "JASNI_ERROR"
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
    
    def __str__(self) -> str:
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status={self.status}, code={self.code!r})"


class AuthenticationError(JasniError):
    """
    Thrown when authentication fails (invalid or missing API key).
    HTTP Status: 401
    """
    
    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, status=401, code="AUTHENTICATION_ERROR")


class NotFoundError(JasniError):
    """
    Thrown when the requested resource is not found.
    HTTP Status: 404
    """
    
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status=404, code="NOT_FOUND")


class ValidationError(JasniError):
    """
    Thrown when request validation fails.
    HTTP Status: 400
    """
    
    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(message, status=400, code="VALIDATION_ERROR")


class RateLimitError(JasniError):
    """
    Thrown when the rate limit is exceeded.
    HTTP Status: 429
    
    Attributes:
        retry_after: Time in seconds until the rate limit resets
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ) -> None:
        super().__init__(message, status=429, code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class ConflictError(JasniError):
    """
    Thrown when there's a conflict (e.g., resource already exists).
    HTTP Status: 409
    """
    
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, status=409, code="CONFLICT")


class ServerError(JasniError):
    """
    Thrown when the server encounters an internal error.
    HTTP Status: 500
    """
    
    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message, status=500, code="SERVER_ERROR")


def create_error_from_response(
    status: int,
    message: str,
    retry_after: Optional[int] = None
) -> JasniError:
    """
    Creates the appropriate error based on HTTP status code.
    
    Args:
        status: HTTP status code
        message: Error message from the API
        retry_after: Optional retry-after header value
    
    Returns:
        Appropriate JasniError subclass instance
    """
    error_map = {
        400: ValidationError,
        401: AuthenticationError,
        404: NotFoundError,
        409: ConflictError,
    }
    
    if status == 429:
        return RateLimitError(message, retry_after)
    
    if status in (500, 502, 503, 504):
        return ServerError(message)
    
    error_class = error_map.get(status)
    if error_class:
        return error_class(message)
    
    return JasniError(message, status)
