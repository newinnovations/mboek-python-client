"""Grootboekrekeningen resource."""

from __future__ import annotations

from mboek._parsers import (
    parse_grootboek_mutatie,
    parse_grootboekrekening,
    parse_grootboekrekening_met_saldo,
)
from mboek.models.grootboekrekeningen import (
    CreateGrootboekrekeningInput,
    GrootboekMutatie,
    GrootboekrekeningMetSaldoResponse,
    GrootboekrekeningResponse,
    UpdateGrootboekrekeningInput,
)
from mboek.resources._base import BaseResource


class GrootboekrekeningenResource(BaseResource):
    """CRUD + utility operations for grootboekrekeningen (chart of accounts).

    Instantiated via :py:meth:`AdministratieScope.grootboekrekeningen`.

    Account types:

    - ``activa`` — assets (balance sheet)
    - ``passiva`` — liabilities and equity (balance sheet)
    - ``kosten`` — costs (P&L)
    - ``opbrengsten`` — revenues (P&L)
    - ``bijzonder`` — extraordinary items (P&L)
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(self) -> list[GrootboekrekeningResponse]:
        """Return all grootboekrekeningen for the administratie.

        Returns:
            List sorted by code ascending.
        """
        return [
            parse_grootboekrekening(d)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen"
            )
        ]

    def get(self, id: int) -> GrootboekrekeningResponse:
        """Return a single grootboekrekening.

        Args:
            id: Grootboekrekening ID.
        """
        return parse_grootboekrekening(
            self._get(f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}")
        )

    def create(
        self, input: CreateGrootboekrekeningInput
    ) -> GrootboekrekeningResponse:
        """Create a new grootboekrekening.

        Args:
            input: Account parameters.
        """
        return parse_grootboekrekening(
            self._post(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen",
                json=input.to_dict(),
            )
        )

    def update(
        self, id: int, input: UpdateGrootboekrekeningInput
    ) -> GrootboekrekeningResponse:
        """Partially update a grootboekrekening.

        Args:
            id: Grootboekrekening ID.
            input: Fields to update.
        """
        return parse_grootboekrekening(
            self._patch(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}",
                json=input.to_dict(),
            )
        )

    def delete(self, id: int) -> None:
        """Permanently delete a grootboekrekening.

        Fails if the account is referenced by existing boekingsregels or BTW codes.

        Args:
            id: Grootboekrekening ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}")

    def seed_rgs(self) -> None:
        """Seed the standard Dutch RGS (Referentie Grootboekschema) chart of accounts.

        Creates ~23 common account categories (1000–4900) if those codes do not
        already exist. Skips any code that is already present. Run
        :py:meth:`~mboek.resources.btw_codes.BtwCodesResource.seed_defaults`
        afterwards to set up linked BTW rekeningen.
        """
        self._post(f"/api/administraties/{self._admin_id}/grootboekrekeningen/seed-rgs")

    def met_saldo(
        self, boekjaar_id: int
    ) -> list[GrootboekrekeningMetSaldoResponse]:
        """Return all grootboekrekeningen enriched with transaction count and balance.

        Includes accounts with zero transactions in the boekjaar (with zeros).
        Useful for filtering the chart of accounts in scripts.

        Args:
            boekjaar_id: Fiscal year to aggregate over.

        Returns:
            One entry per rekening, sorted by code.
        """
        return [
            parse_grootboekrekening_met_saldo(d)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/met-saldo/{boekjaar_id}"
            )
        ]

    def mutaties(
        self, id: int, boekjaar_id: int
    ) -> list[GrootboekMutatie]:
        """Return the full mutation ledger for a single rekening.

        Returns every boekingsregel with its date, dagboek, journal entry
        description, line description, and amount.

        Args:
            id: Grootboekrekening ID.
            boekjaar_id: Fiscal year to query.

        Returns:
            List of mutations ordered by date and ID.
        """
        return [
            parse_grootboek_mutatie(d)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/rekening/{id}/mutaties",
                params={"boekjaar_id": boekjaar_id},
            )
        ]

    def find_by_naam(self, naam: str) -> GrootboekrekeningResponse | None:
        """Find a grootboekrekening by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact account name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.grootboekrekeningen.GrootboekrekeningResponse`,
            or ``None`` if not found.
        """
        return next((r for r in self.list() if r.naam == naam), None)

    def find_by_code(self, code: str) -> GrootboekrekeningResponse | None:
        """Find a grootboekrekening by its account code.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            code: Account code to search for (e.g. ``"1220"``).

        Returns:
            The matching :py:class:`~mboek.models.grootboekrekeningen.GrootboekrekeningResponse`,
            or ``None`` if not found.
        """
        return next((r for r in self.list() if r.code == code), None)
