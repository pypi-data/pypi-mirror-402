"""Base exception classes for GitLab API errors."""

from enum import Enum
from http import HTTPStatus as _HTTPStatus
from typing import Any, ClassVar


class GitLabErrorType(str, Enum):
    """Common GitLab API error types."""

    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    INVALID_TOKEN = "invalid_token"
    REQUEST_FAILED = "request_failed"


class GitLabAPIError(Exception):
    """Custom exception for GitLab API errors with actionable messages."""

    # Status code to error type mapping
    STATUS_TO_ERROR: ClassVar[dict[int, GitLabErrorType]] = {
        _HTTPStatus.NOT_FOUND: GitLabErrorType.NOT_FOUND,
        _HTTPStatus.FORBIDDEN: GitLabErrorType.ACCESS_DENIED,
        _HTTPStatus.UNAUTHORIZED: GitLabErrorType.INVALID_TOKEN,
        _HTTPStatus.BAD_REQUEST: GitLabErrorType.INVALID_REQUEST,
    }

    # Standard error messages
    ERROR_MESSAGES: ClassVar[dict[GitLabErrorType, str]] = {
        GitLabErrorType.NOT_FOUND: "Resource not found",
        GitLabErrorType.ACCESS_DENIED: "Access denied",
        GitLabErrorType.INVALID_REQUEST: "Invalid request",
        GitLabErrorType.SERVER_ERROR: "Server error occurred",
        GitLabErrorType.INVALID_TOKEN: "Invalid token",
        GitLabErrorType.REQUEST_FAILED: "Request failed",
    }

    def __init__(
        self,
        error_type: GitLabErrorType,
        details: dict[str, Any] | None = None,
        code: int | None = None,
    ) -> None:
        """Initialize the GitLab API error.

        Args:
            error_type: The type of error that occurred.
            details: Optional details about the error.
            code: Optional HTTP status code.
        """
        self.error_type = error_type
        self.details = details or {}
        self.code = code

        message = self.ERROR_MESSAGES[error_type]
        if details:
            message = f"{message}: {details}"

        super().__init__(message)

    @classmethod
    def from_response(
        cls, response: Any, details: dict[str, Any] | None = None
    ) -> "GitLabAPIError":
        """Create an error from an HTTP response.

        Args:
            response: The HTTP response object.
            details: Additional error details.

        Returns:
            A GitLabAPIError instance.
        """
        error_type = cls.STATUS_TO_ERROR.get(
            response.status_code, GitLabErrorType.SERVER_ERROR
        )
        error_details = details or {}

        if not error_details.get("message"):
            try:
                error_data = response.json()
                error_details["message"] = error_data.get("message", response.text)
            except Exception:
                error_details["message"] = response.text

        return cls(error_type, error_details, code=response.status_code)


class GitLabAuthError(GitLabAPIError):
    """Raised when GitLab authentication fails."""

    def __init__(self) -> None:
        """Initialize with standard auth error message."""
        super().__init__(
            GitLabErrorType.INVALID_TOKEN,
            {"message": "GITLAB_PERSONAL_ACCESS_TOKEN environment variable is not set"},
            code=_HTTPStatus.UNAUTHORIZED,
        )
