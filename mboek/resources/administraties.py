"""Administraties resource."""

from __future__ import annotations

from mboek._parsers import parse_administratie
from mboek.models.administraties import Administratie
from mboek.resources._base import BaseResource


class AdministratiesResource(BaseResource):
    """CRUD operations for administraties (company administrations).

    Access via :py:attr:`MboekClient.administraties`.

    Each user sees only the administrations they own.
    """

    def list(self) -> list[Administratie]:
        """Return all administraties owned by the authenticated user.

        Returns:
            List sorted alphabetically by name.
        """
        return [parse_administratie(d) for d in self._get("/api/administraties")]

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
        naam: str | None = None,
        beschrijving: str | None = None,
        kvk_nummer: str | None = None,
        btw_nummer: str | None = None,
        adres: str | None = None,
        active: bool | None = None,
        huidig_boekjaar_id: int | None = None,
    ) -> Administratie:
        """Partially update an administratie.

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
        if naam is not None:
            data["naam"] = naam
        if beschrijving is not None:
            data["beschrijving"] = beschrijving
        if kvk_nummer is not None:
            data["kvk_nummer"] = kvk_nummer
        if btw_nummer is not None:
            data["btw_nummer"] = btw_nummer
        if adres is not None:
            data["adres"] = adres
        if active is not None:
            data["active"] = active
        if huidig_boekjaar_id is not None:
            data["huidig_boekjaar_id"] = huidig_boekjaar_id
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

    def find_by_naam(self, naam: str) -> Administratie | None:
        """Find an administratie by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.administraties.Administratie`,
            or ``None`` if not found.
        """
        return next((a for a in self.list() if a.naam == naam), None)
