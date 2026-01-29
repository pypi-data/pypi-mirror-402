"""Custom exceptions for HelloLedger SDK."""


class HelloLedgerError(Exception):
    """Base exception for all HelloLedger errors."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(HelloLedgerError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", status_code: int = 401, response_body: dict = None):
        super().__init__(message, status_code, response_body)


class APIError(HelloLedgerError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message, status_code, response_body)


class NotFoundError(HelloLedgerError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", status_code: int = 404, response_body: dict = None):
        super().__init__(message, status_code, response_body)


class PermissionError(HelloLedgerError):
    """Raised when the API key doesn't have permission to access a resource."""

    def __init__(
        self, message: str = "Permission denied", status_code: int = 403, response_body: dict = None
    ):
        super().__init__(message, status_code, response_body)
