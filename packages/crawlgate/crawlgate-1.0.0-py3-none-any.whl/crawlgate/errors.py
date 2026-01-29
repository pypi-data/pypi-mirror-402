"""
CrawlGate SDK Error Classes
"""

from typing import Optional


class CrawlGateError(Exception):
    """Base exception for CrawlGate SDK errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        response: Optional[dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.response = response

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CrawlGateError):
    """Raised when API key is invalid or missing (401)"""
    pass


class RateLimitError(CrawlGateError):
    """Raised when rate limit is exceeded (429)"""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        code: Optional[str] = None,
        response: Optional[dict] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, status_code, code, response)
        self.retry_after = retry_after


class ValidationError(CrawlGateError):
    """Raised when request parameters are invalid (400)"""
    pass


class NotFoundError(CrawlGateError):
    """Raised when requested resource is not found (404)"""
    pass


class ServerError(CrawlGateError):
    """Raised when server returns an error (500+)"""
    pass


class TimeoutError(CrawlGateError):
    """Raised when request or job times out"""
    pass


class JobFailedError(CrawlGateError):
    """Raised when an async job fails"""
    pass
