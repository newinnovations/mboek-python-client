"""Exception hierarchy for the mBoek API client."""

from __future__ import annotations

from typing import Any


class MboekError(Exception):
    """Base exception for all mBoek client errors.

    Attributes:
        status_code: HTTP status code returned by the server, or ``None`` for
            transport-level failures.
        detail: Parsed server response detail, raw response text, or the
            underlying transport/parsing exception.
    """

    def __init__(
        self, message: str, *, status_code: int | None = None, detail: Any = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.args[0]!r},"
            f" status_code={self.status_code!r}, detail={self.detail!r})"
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


class ScopeError(ValueError):
    """Raised when a method or property requires a scope that has not been set.

    This is a programming error, not an HTTP error — no network call is involved.

    Examples::

        dagboek = client.administratie(1).dagboeken.list(code="BANK")[0]
        dagboek.boekingen.list()      # raises ScopeError — no boekjaar scope

        gbr = client.administratie(1).grootboekrekeningen.list(code=1220)[0]
        gbr.saldo                     # raises ScopeError — no boekjaar scope

    Fix by adding the required scope::

        dagboek_scoped = dagboek.with_boekjaar(id=10)
        dagboek_scoped.boekingen.list()   # ✓ works

        gbr_scoped = gbr.with_boekjaar(id=10)
        gbr_scoped.saldo                  # ✓ fetches on first access
    """
