"""Lawgorithm SDK exceptions."""


class LawgorithmError(Exception):
    """Base exception for Lawgorithm SDK."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(LawgorithmError):
    """Raised when authentication fails (401/403)."""

    pass


class NotFoundError(LawgorithmError):
    """Raised when a resource is not found (404)."""

    pass


class ValidationError(LawgorithmError):
    """Raised when request validation fails (422)."""

    def __init__(self, message: str, errors: list[dict] | None = None) -> None:
        super().__init__(message, status_code=422)
        self.errors = errors or []


class ComplianceError(LawgorithmError):
    """Raised when a compliance check fails in strict mode."""

    def __init__(self, message: str, issues: list[dict] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


class RateLimitError(LawgorithmError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ServerError(LawgorithmError):
    """Raised when server returns 5xx error."""

    pass
