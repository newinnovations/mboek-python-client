"""MboekClient — main entry point for the mBoek API client."""

from __future__ import annotations

import os
from typing import Any

import requests

from mboek._exceptions import (
    AuthError,
    ConflictError,
    ForbiddenError,
    MboekError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from mboek.models.auth import AuthToken


class MboekClient:
    """Synchronous HTTP client for the mBoek bookkeeping API.

    Resources are organised hierarchically. Start by obtaining an
    :py:class:`~mboek.resources._admin_scope.AdministratieScope` via
    :py:meth:`administratie`, then navigate to child resources::

        from mboek import MboekClient

        with MboekClient("http://localhost:3000", "admin", "geheim") as client:
            admins = client.administraties.list()
            admin = client.administratie(admins[0].id)

            boekjaren = admin.boekjaren.list()
            dagboek = admin.dagboek(20).with_boekjaar(id=10)
            boekingen = dagboek.boekingen.list()

    **Environment variables**::

        # export MBOEK_URL=http://localhost:3000
        # export MBOEK_USERNAME=admin
        # export MBOEK_PASSWORD=geheim

        with MboekClient() as client:
            admins = client.administraties.list()

    Environment variables:

    - ``MBOEK_URL`` — backend base URL (fallback when ``base_url`` is ``None``)
    - ``MBOEK_USERNAME`` — username (fallback when ``username`` is ``None``)
    - ``MBOEK_PASSWORD`` — password (fallback when ``password`` is ``None``)

    Args:
        base_url: Base URL of the mBoek backend (no trailing slash). Falls back
            to the ``MBOEK_URL`` environment variable, then
            ``http://localhost:3000``.
        username: If provided together with ``password`` (either directly or via
            environment variables), :py:meth:`login` is called automatically
            during construction.
        password: Password for auto-login.
        timeout: Default request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *,
        timeout: int = 30,
    ) -> None:
        resolved_url = (
            base_url or os.environ.get("MBOEK_URL") or "http://localhost:3000"
        )
        resolved_username = username or os.environ.get("MBOEK_USERNAME")
        resolved_password = password or os.environ.get("MBOEK_PASSWORD")

        self._base_url = resolved_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._token: str | None = None
        self._login_response: AuthToken | None = None

        # Lazily-initialised resource managers
        self._administraties = None
        self._boekingen = None
        self._export_import = None
        self._maintenance = None

        # Per-admin grootboekrekening list cache (keyed by admin_id).
        # Populated by GrootboekrekeningenResource.list() and cleared via clear_cache().
        self._gbr_cache: dict[int, list] = {}

        if resolved_username is not None and resolved_password is not None:
            self.login(resolved_username, resolved_password)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "MboekClient":
        return self

    def __exit__(self, *_: object) -> None:
        if self._token is not None:
            try:
                self.logout()
            except MboekError:
                pass
        self._session.close()

    # ── Authentication ────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> AuthToken:
        """Authenticate and store the bearer token for subsequent requests.

        Args:
            username: mBoek username (``gebruikersnaam``).
            password: mBoek password (``wachtwoord``).

        Returns:
            :py:class:`~mboek.models.auth.AuthToken`.

        Raises:
            :py:class:`~mboek._exceptions.AuthError`: Invalid credentials.
            :py:class:`~mboek._exceptions.RateLimitError`: Too many attempts.
        """
        response = self._login_response = self.auth.login(username, password)
        self._token = response.token
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})
        return response

    def logout(self) -> None:
        """Revoke the current token server-side and clear the stored token.

        Raises:
            :py:class:`~mboek._exceptions.AuthError`: Not authenticated.
        """
        self.auth.logout()
        self._token = None
        self._session.headers.pop("Authorization", None)

    @property
    def token(self) -> str | None:
        """The current JWT bearer token, or ``None`` if not logged in."""
        return self._token

    # ── Resource properties ───────────────────────────────────────────────────

    @property
    def auth(self):
        """Authentication resource (:py:class:`~mboek.resources.auth.AuthResource`)."""
        from mboek.resources.auth import AuthResource

        # Auth resource is instantiated fresh each time to avoid circular
        # dependency during __init__ before self is fully initialised.
        return AuthResource(self)

    @property
    def administraties(self):
        """Administraties resource (:py:class:`~mboek.resources.administraties.AdministratiesResource`)."""
        if self._administraties is None:
            from mboek.resources.administraties import AdministratiesResource

            self._administraties = AdministratiesResource(self)
        return self._administraties

    @property
    def boekingen(self):
        """Boekingen resource — get/update/delete by ID (:py:class:`~mboek.resources.boekingen.BoekingenResource`).

        To list or create boekingen, use the boekjaar-scoped access::

            bj = client.administratie(1).boekjaar(10)
            entries = bj.dagboek(20).boekingen.list()
        """
        if self._boekingen is None:
            from mboek.resources.boekingen import BoekingenResource

            self._boekingen = BoekingenResource(self)
        return self._boekingen

    @property
    def export_import(self):
        """Top-level export/import resource (:py:class:`~mboek.resources.export_import.ExportImportResource`).

        Only contains :py:meth:`~mboek.resources.export_import.ExportImportResource.import_administratie`.
        All other export/import operations are available via
        :py:attr:`~mboek.resources._admin_scope.AdministratieScope.export_import`.
        """
        if self._export_import is None:
            from mboek.resources.export_import import ExportImportResource

            self._export_import = ExportImportResource(self)
        return self._export_import

    @property
    def maintenance(self):
        """Maintenance resource (:py:class:`~mboek.resources.maintenance.MaintenanceResource`)."""
        if self._maintenance is None:
            from mboek.resources.maintenance import MaintenanceResource

            self._maintenance = MaintenanceResource(self)
        return self._maintenance

    # ── Scoped access ─────────────────────────────────────────────────────────

    def administratie(self, id: int | None = None, *, name: str | None = None):
        """Return an :py:class:`~mboek.resources._admin_scope.AdministratieScope`.

        Pass either the numeric ``id`` (no HTTP call) or a ``name`` to
        look up the administratie by exact name (one HTTP call)::

            admin = client.administratie(1)
            admin = client.administratie(name="Demo BV")

            boekjaren = admin.boekjaren.list()
            dagboek = admin.dagboek(20)

        Args:
            id: Administratie ID. No HTTP call is made.
            name: Exact administratie name (case-sensitive). Performs a
                :py:meth:`~mboek.resources.administraties.AdministratiesResource.list`
                lookup request.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` given but no
                matching administratie found.
            :py:exc:`ValueError`: Neither or both of ``id`` and ``name``
                provided.
        """
        provided = sum(x is not None for x in [id, name])
        if provided != 1:
            raise ValueError("Provide exactly one of: id, name")
        if name is not None:
            found = self.administraties._require_single_match(
                self.administraties.list(name=name),
                not_found_message=f"Administratie '{name}' not found",
                multiple_message=f"Multiple administraties named '{name}' found",
            )
            id = found.id
        from mboek.resources._admin_scope import AdministratieScope

        if id is None:
            raise AssertionError(
                "administratie() could not resolve an administratie ID"
            )
        return AdministratieScope(self, id)

    # ── Internal HTTP helpers ─────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict | None = None,
        files: dict | None = None,
        data: dict | None = None,
    ) -> Any:
        """Send an authenticated HTTP request and return the parsed JSON body.

        Raises appropriate :py:exc:`~mboek._exceptions.MboekError` subclasses
        based on the response status code.
        """
        url = self._base_url + path
        resp = self._session.request(
            method,
            url,
            json=json,
            params=params,
            files=files,
            data=data,
            timeout=self._timeout,
        )
        return self._handle_response(resp)

    def _request_no_auth(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict | None = None,
    ) -> Any:
        """Send an unauthenticated request (used for the login endpoint)."""
        url = self._base_url + path
        resp = requests.request(
            method,
            url,
            json=json,
            params=params,
            timeout=self._timeout,
        )
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response) -> Any:
        """Raise typed exceptions for error responses, return body for 2xx."""
        if resp.status_code in (200, 201):
            if resp.content:
                return resp.json()
            return None
        if resp.status_code == 204:
            return None

        # Try to extract a detail message from the response body.
        detail: Any = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text or None

        msg = f"HTTP {resp.status_code}"
        if detail:
            if isinstance(detail, dict):
                msg = detail.get("error", detail.get("message", str(detail)))
            else:
                msg = str(detail)

        status = resp.status_code
        if status == 401:
            raise AuthError(msg, status_code=status, detail=detail)
        if status == 403:
            raise ForbiddenError(msg, status_code=status, detail=detail)
        if status == 404:
            raise NotFoundError(msg, status_code=status, detail=detail)
        if status == 409:
            raise ConflictError(msg, status_code=status, detail=detail)
        if status == 422:
            raise ValidationError(msg, status_code=status, detail=detail)
        if status == 429:
            raise RateLimitError(msg, status_code=status, detail=detail)
        raise MboekError(msg, status_code=status, detail=detail)
