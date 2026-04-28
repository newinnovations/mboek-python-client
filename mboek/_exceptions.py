"""Exception hierarchy for the mBoek API client."""

from __future__ import annotations

from typing import Any


class MboekError(Exception):
    """Base exception for all mBoek client errors.

    Attributes:
        status_code: HTTP status code returned by the server, or ``None`` for
            network-level errors.
        detail: Human-readable error message from the server response body.
    """

    def __init__(
        self, message: str, *, status_code: int | None = None, detail: Any = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.args[0]!r}, status_code={self.status_code!r})"
        )


class AuthError(MboekError):
    """Raised when the server returns **401 Unauthorized**.

    This typically means the token is missing, expired, or has been revoked.
    Re-authenticate by calling :py:meth:`MboekClient.login` again.
    """


class ForbiddenError(MboekError):
    """Raised when the server returns **403 Forbidden**.

    The authenticated user does not own the requested resource.
    """


class NotFoundError(MboekError):
    """Raised when the server returns **404 Not Found**."""


class ValidationError(MboekError):
    """Raised when the server returns **422 Unprocessable Entity**.

    The ``detail`` attribute contains the server's validation error payload.
    """


class ConflictError(MboekError):
    """Raised when the server returns **409 Conflict**.

    For example, trying to close a boekjaar that is already closed.
    """


class RateLimitError(MboekError):
    """Raised when the server returns **429 Too Many Requests**.

    The login endpoint applies rate limiting. Wait before retrying.
    """
