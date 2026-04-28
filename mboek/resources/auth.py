"""Authentication resource."""

from __future__ import annotations

from mboek._parsers import parse_login
from mboek.models.auth import AuthToken
from mboek.resources._base import BaseResource


class AuthResource(BaseResource):
    """Authentication endpoints.

    Normally you do not call these methods directly — :py:class:`MboekClient`
    handles login/logout for you. They are exposed for advanced usage.
    """

    def login(self, username: str, password: str) -> AuthToken:
        """Authenticate and obtain a JWT bearer token.

        Args:
            username: mBoek username (``gebruikersnaam``).
            password: mBoek password (``wachtwoord``).

        Returns:
            :py:class:`~mboek.models.auth.AuthToken` containing the token
            and its expiry time.

        Raises:
            :py:class:`~mboek._exceptions.AuthError`: Invalid credentials.
            :py:class:`~mboek._exceptions.RateLimitError`: Too many attempts.
        """
        data = self._client._request_no_auth(
            "POST",
            "/api/auth/login",
            json={"gebruikersnaam": username, "wachtwoord": password},
        )
        return parse_login(data)

    def logout(self) -> None:
        """Revoke the current bearer token server-side.

        After calling this, the current token is rejected by the server even
        if it has not expired yet.

        Raises:
            :py:class:`~mboek._exceptions.AuthError`: Not authenticated.
        """
        self._post("/api/auth/logout")

    def me(self) -> dict:
        """Return the currently authenticated user's info.

        Returns:
            A dict with ``gebruikersnaam`` and ``sub`` fields.

        Raises:
            :py:class:`~mboek._exceptions.AuthError`: Not authenticated.
        """
        return self._get("/api/auth/me")
