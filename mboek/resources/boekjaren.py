"""Boekjaren resource."""

from __future__ import annotations

import builtins
from datetime import date

from mboek._parsers import parse_boekjaar
from mboek.models.boekjaren import Boekjaar
from mboek.resources._base import BaseResource


class BoekjarenResource(BaseResource):
    """CRUD + lifecycle operations for boekjaren (fiscal years).

    Instantiated via :py:meth:`AdministratieScope.boekjaren`.
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Boekjaar]:
        """Return boekjaren for the administratie.

        All filters are exact matches and are combined with ``AND`` semantics.
        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically before client-side filtering is applied.

        Returns:
            List sorted by start date ascending.
        """
        filtered = id is not None or name is not None
        items = [
            parse_boekjaar(d, client=self._client)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/boekjaren",
                limit=None if filtered else limit,
                offset=None if filtered else offset,
            )
        ]
        if id is not None:
            items = [item for item in items if item.id == id]
        if name is not None:
            items = [item for item in items if item.naam == name]
        if filtered:
            return self._slice_items(items, limit=limit, offset=offset)
        return items

    def get(self, id: int) -> Boekjaar:
        """Return a single boekjaar.

        Args:
            id: Boekjaar ID.
        """
        return parse_boekjaar(
            self._get(f"/api/administraties/{self._admin_id}/boekjaren/{id}"),
            client=self._client,
        )

    def create(self, naam: str, start_datum: date, eind_datum: date) -> Boekjaar:
        """Create a new boekjaar.

        New boekjaren start with status ``open``.

        Args:
            naam: Display name (e.g. ``"2024"``).
            start_datum: First day of the fiscal year.
            eind_datum: Last day of the fiscal year.
        """
        data = {
            "naam": naam,
            "start_datum": start_datum.isoformat(),
            "eind_datum": eind_datum.isoformat(),
        }
        return parse_boekjaar(
            self._post(f"/api/administraties/{self._admin_id}/boekjaren", json=data),
            client=self._client,
        )

    def update(
        self,
        id: int,
        *,
        naam: str | None = None,
        start_datum: date | None = None,
        eind_datum: date | None = None,
    ) -> Boekjaar:
        """Partially update a boekjaar's name or dates.

        To change status use :py:meth:`afsluiten` or :py:meth:`heropenen`.

        Args:
            id: Boekjaar ID.
            naam: New display name.
            start_datum: New start date.
            eind_datum: New end date.
        """
        data: dict = {}
        if naam is not None:
            data["naam"] = naam
        if start_datum is not None:
            data["start_datum"] = start_datum.isoformat()
        if eind_datum is not None:
            data["eind_datum"] = eind_datum.isoformat()
        return parse_boekjaar(
            self._patch(
                f"/api/administraties/{self._admin_id}/boekjaren/{id}", json=data
            ),
            client=self._client,
        )

    def delete(self, id: int) -> None:
        """Permanently delete a boekjaar, all its boekingen, and related BTW aangiften.

        .. warning::
            Irreversible.

        Args:
            id: Boekjaar ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/boekjaren/{id}")

    def afsluiten(self, id: int) -> Boekjaar:
        """Close a boekjaar (transition ``open`` → ``gesloten``).

        A closed boekjaar no longer accepts new boekingen. This is a
        prerequisite for finalising a BTW-aangifte via ``vastleggen``.

        Args:
            id: Boekjaar ID.

        Raises:
            :py:class:`~mboek._exceptions.ConflictError`: Already closed.
        """
        return parse_boekjaar(
            self._post(
                f"/api/administraties/{self._admin_id}/boekjaren/{id}/afsluiten"
            ),
            client=self._client,
        )

    def heropenen(self, id: int) -> Boekjaar:
        """Reopen a gesloten boekjaar (transition ``gesloten`` → ``open``).

        Blocked if there are any definitieve BTW-aangiften for this boekjaar.

        Args:
            id: Boekjaar ID.

        Raises:
            :py:class:`~mboek._exceptions.ConflictError`: Not closed or has
                definitieve BTW-aangiften.
        """
        return parse_boekjaar(
            self._post(
                f"/api/administraties/{self._admin_id}/boekjaren/{id}/heropenen"
            ),
            client=self._client,
        )

    def set_huidig(self, id: int) -> Boekjaar:
        """Set a boekjaar as the current (default) boekjaar of its administratie.

        The current boekjaar is used as a default in endpoints that accept an
        optional ``boekjaar_id`` query parameter (e.g. dagboek werkstatus).

        Args:
            id: Boekjaar ID to set as current.
        """
        return parse_boekjaar(
            self._post(
                f"/api/administraties/{self._admin_id}/boekjaren/{id}/set-huidig"
            ),
            client=self._client,
        )
