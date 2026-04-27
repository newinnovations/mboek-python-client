"""Dagboeken resource."""

from __future__ import annotations

from mboek._parsers import parse_dagboek, parse_werkstatus
from mboek.models.dagboeken import (
    CreateDagboekInput,
    DagboekResponse,
    DagboekWerkStatus,
    UpdateDagboekInput,
)
from mboek.resources._base import BaseResource


class DagboekenResource(BaseResource):
    """CRUD + werkstatus operations for dagboeken (journals / sub-ledgers).

    Instantiated via :py:meth:`AdministratieScope.dagboeken`.

    Dagboek types:

    - ``bank`` — bank account (linked to a balance-sheet rekening + optional IBAN)
    - ``kas`` — cash book
    - ``inkoop`` — purchase journal
    - ``verkoop`` — sales journal
    - ``memoriaal`` — general journal (full double-entry)
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(self) -> list[DagboekResponse]:
        """Return all dagboeken for the administratie.

        Returns:
            List sorted by code ascending.
        """
        return [
            parse_dagboek(d)
            for d in self._get(f"/api/administraties/{self._admin_id}/dagboeken")
        ]

    def get(self, id: int) -> DagboekResponse:
        """Return a single dagboek.

        Args:
            id: Dagboek ID.
        """
        return parse_dagboek(
            self._get(f"/api/administraties/{self._admin_id}/dagboeken/{id}")
        )

    def create(self, input: CreateDagboekInput) -> DagboekResponse:
        """Create a new dagboek.

        Args:
            input: Dagboek parameters.
        """
        return parse_dagboek(
            self._post(f"/api/administraties/{self._admin_id}/dagboeken", json=input.to_dict())
        )

    def update(self, id: int, input: UpdateDagboekInput) -> DagboekResponse:
        """Partially update a dagboek.

        Args:
            id: Dagboek ID.
            input: Fields to update.
        """
        return parse_dagboek(
            self._patch(
                f"/api/administraties/{self._admin_id}/dagboeken/{id}", json=input.to_dict()
            )
        )

    def delete(self, id: int) -> None:
        """Permanently delete a dagboek.

        Fails if the dagboek has existing boekingen.

        Args:
            id: Dagboek ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/dagboeken/{id}")

    def werkstatus(
        self, boekjaar_id: int | None = None
    ) -> list[DagboekWerkStatus]:
        """Return per-dagboek work-status counts.

        Returns the number of unprocessed bank imports (``onverwerkt``) and
        unconfirmed auto-booked entries (``te_bevestigen``) for each dagboek.

        Args:
            boekjaar_id: Fiscal year to query. Defaults to the administratie's
                ``huidig_boekjaar_id`` when omitted.

        Returns:
            One :py:class:`~mboek.models.dagboeken.DagboekWerkStatus` per
            dagboek that has non-zero counts.
        """
        params: dict = {}
        if boekjaar_id is not None:
            params["boekjaar_id"] = boekjaar_id
        return [
            parse_werkstatus(d)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/dagboeken/werkstatus", params=params
            )
        ]

    def find_by_naam(self, naam: str) -> DagboekResponse | None:
        """Find a dagboek by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact dagboek name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.dagboeken.DagboekResponse`,
            or ``None`` if not found.
        """
        return next((d for d in self.list() if d.naam == naam), None)

    def find_by_code(self, code: str) -> DagboekResponse | None:
        """Find a dagboek by its short code.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            code: Short dagboek code to search for (e.g. ``"BANK"``).
                The comparison is case-insensitive.

        Returns:
            The matching :py:class:`~mboek.models.dagboeken.DagboekResponse`,
            or ``None`` if not found.
        """
        code_upper = code.upper()
        return next((d for d in self.list() if d.code.upper() == code_upper), None)
