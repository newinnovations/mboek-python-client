"""Administraties resource."""

from __future__ import annotations

import builtins

from mboek._parsers import parse_administratie
from mboek._unset import UNSET, UnsetType
from mboek.models.administraties import Administratie
from mboek.resources._base import BaseResource


class AdministratiesResource(BaseResource):
    """CRUD operations for administraties (company administrations).

    Access via :py:attr:`MboekClient.administraties`.

    Each user sees only the administrations they own.
    """

    def list(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Administratie]:
        """Return administraties owned by the authenticated user.

        All filters are exact matches and are combined with ``AND`` semantics.
        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically before client-side filtering is applied.

        Returns:
            List sorted alphabetically by name.
        """
        filtered = id is not None or name is not None
        items = [
            parse_administratie(d)
            for d in self._get_paginated(
                "/api/administraties",
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

    def get(self, id: int) -> Administratie:
        """Return a single administratie by ID.

        Args:
            id: Administratie ID.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: Not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        return parse_administratie(self._get(f"/api/administraties/{id}"))

    def create(
        self,
        naam: str,
        *,
        beschrijving: str | None = None,
        kvk_nummer: str | None = None,
        btw_nummer: str | None = None,
        adres: str | None = None,
    ) -> Administratie:
        """Create a new administratie.

        Args:
            naam: Name of the administration (required).
            beschrijving: Optional description.
            kvk_nummer: Optional KvK registration number.
            btw_nummer: Optional VAT registration number.
            adres: Optional postal address.

        Returns:
            The newly created administratie.
        """
        data: dict = {"naam": naam}
        if beschrijving is not None:
            data["beschrijving"] = beschrijving
        if kvk_nummer is not None:
            data["kvk_nummer"] = kvk_nummer
        if btw_nummer is not None:
            data["btw_nummer"] = btw_nummer
        if adres is not None:
            data["adres"] = adres
        return parse_administratie(self._post("/api/administraties", json=data))

    def update(
        self,
        id: int,
        *,
        naam: str | None | UnsetType = UNSET,
        beschrijving: str | None | UnsetType = UNSET,
        kvk_nummer: str | None | UnsetType = UNSET,
        btw_nummer: str | None | UnsetType = UNSET,
        adres: str | None | UnsetType = UNSET,
        active: bool | None | UnsetType = UNSET,
        huidig_boekjaar_id: int | None | UnsetType = UNSET,
    ) -> Administratie:
        """Partially update an administratie.

        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

        Args:
            id: Administratie ID.
            naam: New name.
            beschrijving: New description.
            kvk_nummer: New KvK number.
            btw_nummer: New BTW number.
            adres: New address.
            active: Set active/inactive.
            huidig_boekjaar_id: Set the default boekjaar.

        Returns:
            The updated administratie.
        """
        data: dict = {}
        self._set_patch_value(data, "naam", naam)
        self._set_patch_value(data, "beschrijving", beschrijving)
        self._set_patch_value(data, "kvk_nummer", kvk_nummer)
        self._set_patch_value(data, "btw_nummer", btw_nummer)
        self._set_patch_value(data, "adres", adres)
        self._set_patch_value(data, "active", active)
        self._set_patch_value(data, "huidig_boekjaar_id", huidig_boekjaar_id)
        return parse_administratie(self._patch(f"/api/administraties/{id}", json=data))

    def delete(self, id: int) -> None:
        """Permanently delete an administratie and all its associated data.

        .. warning::
            This is **irreversible** — all boekjaren, dagboeken, boekingen,
            BTW codes, and grootboekrekeningen are deleted.

        Args:
            id: Administratie ID.
        """
        self._delete(f"/api/administraties/{id}")
