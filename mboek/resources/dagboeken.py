"""Dagboeken resource."""

from __future__ import annotations

from mboek._parsers import parse_dagboek, parse_werkstatus
from mboek.models.dagboeken import (
    Dagboek,
    DagboekWerkStatus,
    NewDagboek,
    UpdateDagboek,
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

    def list(self) -> list[Dagboek]:
        """Return all dagboeken for the administratie.

        Returns:
            List sorted by code ascending.
        """
        return [
            parse_dagboek(d, client=self._client)
            for d in self._get(f"/api/administraties/{self._admin_id}/dagboeken")
        ]

    def get(self, id: int) -> Dagboek:
        """Return a single dagboek.

        Args:
            id: Dagboek ID.
        """
        return parse_dagboek(
            self._get(f"/api/administraties/{self._admin_id}/dagboeken/{id}"),
            client=self._client,
        )

    def create(self, input: NewDagboek) -> Dagboek:
        """Create a new dagboek.

        A grootboekrekening may be specified via ``grootboekrekening_naam`` or
        ``grootboekrekening_code`` in addition to the numeric
        ``grootboekrekening_id``; the ID is resolved automatically.

        Args:
            input: Dagboek parameters.
        """
        if input.grootboekrekening_id is None and (
            input.grootboekrekening_naam or input.grootboekrekening_code
        ):
            input.grootboekrekening_id = self._resolve_rekening_id(
                self._admin_id,
                naam=input.grootboekrekening_naam,
                code=input.grootboekrekening_code,
            )
        return parse_dagboek(
            self._post(
                f"/api/administraties/{self._admin_id}/dagboeken", json=input.to_dict()
            ),
            client=self._client,
        )

    def update(self, id: int, input: UpdateDagboek) -> Dagboek:
        """Partially update a dagboek.

        A grootboekrekening may be specified via ``grootboekrekening_naam`` or
        ``grootboekrekening_code`` in addition to the numeric
        ``grootboekrekening_id``; the ID is resolved automatically.

        Args:
            id: Dagboek ID.
            input: Fields to update.
        """
        if input.grootboekrekening_id is None and (
            input.grootboekrekening_naam or input.grootboekrekening_code
        ):
            input.grootboekrekening_id = self._resolve_rekening_id(
                self._admin_id,
                naam=input.grootboekrekening_naam,
                code=input.grootboekrekening_code,
            )
        return parse_dagboek(
            self._patch(
                f"/api/administraties/{self._admin_id}/dagboeken/{id}",
                json=input.to_dict(),
            ),
            client=self._client,
        )

    def delete(self, id: int) -> None:
        """Permanently delete a dagboek.

        Fails if the dagboek has existing boekingen.

        Args:
            id: Dagboek ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/dagboeken/{id}")

    def werkstatus(self, boekjaar_id: int | None = None) -> list[DagboekWerkStatus]:
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
                f"/api/administraties/{self._admin_id}/dagboeken/werkstatus",
                params=params,
            )
        ]

    def find_by_naam(self, naam: str) -> Dagboek | None:
        """Find a dagboek by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact dagboek name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.dagboeken.Dagboek`,
            or ``None`` if not found.
        """
        return next((d for d in self.list() if d.naam == naam), None)

    def find_by_code(self, code: str) -> Dagboek | None:
        """Find a dagboek by its short code.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            code: Short dagboek code to search for (e.g. ``"BANK"``).
                The comparison is case-insensitive.

        Returns:
            The matching :py:class:`~mboek.models.dagboeken.Dagboek`,
            or ``None`` if not found.
        """
        code_upper = code.upper()
        return next((d for d in self.list() if d.code.upper() == code_upper), None)
