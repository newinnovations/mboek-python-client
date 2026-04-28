"""Administraties resource."""

from __future__ import annotations

from mboek._parsers import parse_administratie
from mboek.models.administraties import (
    AdministratieResponse,
    NewAdministratie,
    UpdateAdministratie,
)
from mboek.resources._base import BaseResource


class AdministratiesResource(BaseResource):
    """CRUD operations for administraties (company administrations).

    Access via :py:attr:`MboekClient.administraties`.

    Each user sees only the administrations they own.
    """

    def list(self) -> list[AdministratieResponse]:
        """Return all administraties owned by the authenticated user.

        Returns:
            List sorted alphabetically by name.
        """
        return [parse_administratie(d) for d in self._get("/api/administraties")]

    def get(self, id: int) -> AdministratieResponse:
        """Return a single administratie by ID.

        Args:
            id: Administratie ID.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: Not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        return parse_administratie(self._get(f"/api/administraties/{id}"))

    def create(self, input: NewAdministratie) -> AdministratieResponse:
        """Create a new administratie.

        Args:
            input: Creation parameters.

        Returns:
            The newly created administratie.
        """
        return parse_administratie(
            self._post("/api/administraties", json=input.to_dict())
        )

    def update(self, id: int, input: UpdateAdministratie) -> AdministratieResponse:
        """Partially update an administratie.

        Args:
            id: Administratie ID.
            input: Fields to update (omit fields you want to leave unchanged).

        Returns:
            The updated administratie.
        """
        return parse_administratie(
            self._patch(f"/api/administraties/{id}", json=input.to_dict())
        )

    def delete(self, id: int) -> None:
        """Permanently delete an administratie and all its associated data.

        .. warning::
            This is **irreversible** — all boekjaren, dagboeken, boekingen,
            BTW codes, and grootboekrekeningen are deleted.

        Args:
            id: Administratie ID.
        """
        self._delete(f"/api/administraties/{id}")

    def find_by_naam(self, naam: str) -> AdministratieResponse | None:
        """Find an administratie by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.administraties.AdministratieResponse`,
            or ``None`` if not found.
        """
        return next((a for a in self.list() if a.naam == naam), None)
