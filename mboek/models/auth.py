"""Authentication models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LoginResponse:
    """Response returned by ``POST /api/auth/login``.

    Attributes:
        token: Signed JWT bearer token. Pass this in the
            ``Authorization: Bearer <token>`` header for all subsequent requests.
        gebruikersnaam: The username of the authenticated user.
        expires_at: UTC datetime when the token expires.
    """

    token: str
    gebruikersnaam: str
    expires_at: datetime
