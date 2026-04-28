"""Grootboekrekeningen resource."""

from __future__ import annotations

from mboek._parsers import (
    parse_grootboek_mutatie,
    parse_grootboekrekening,
    parse_grootboekrekening_met_saldo,
)
from mboek.models._enums import RekeningCategorie, RekeningType
from mboek.models.grootboekrekeningen import (
    GrootboekMutatie,
    Grootboekrekening,
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

    def list(self, *, refresh: bool = False) -> list[Grootboekrekening]:
        """Return all grootboekrekeningen for the administratie.

        Results are cached on the client for the lifetime of the session (keyed
        by admin ID).  Call ``list(refresh=True)`` or :py:meth:`clear_cache` to
        force a fresh fetch.

        Args:
            refresh: When ``True``, bypass the cache and fetch from the API.

        Returns:
            List sorted by code ascending.
        """
        cache = self._client._gbr_cache
        if not refresh and self._admin_id in cache:
            return cache[self._admin_id]
        result = [
            parse_grootboekrekening(d, client=self._client)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen"
            )
        ]
        cache[self._admin_id] = result
        return result

    def get(self, id: int) -> Grootboekrekening:
        """Return a single grootboekrekening.

        Args:
            id: Grootboekrekening ID.
        """
        return parse_grootboekrekening(
            self._get(f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}"),
            client=self._client,
        )

    def create(
        self,
        code: str,
        naam: str,
        rekening_type: RekeningType,
        categorie: RekeningCategorie,
        *,
        rgs_code: str | None = None,
        parent_id: int | None = None,
        default_btw_id: int | None = None,
    ) -> Grootboekrekening:
        """Create a new grootboekrekening.

        Args:
            code: Account code (must be unique within the administratie).
            naam: Account name.
            rekening_type: Account type.
            categorie: Statement category.
            rgs_code: Optional RGS code.
            parent_id: Optional parent account ID.
            default_btw_id: Optional default BTW code.
        """
        data: dict = {
            "code": code,
            "naam": naam,
            "rekening_type": rekening_type.value,
            "categorie": categorie.value,
        }
        if rgs_code is not None:
            data["rgs_code"] = rgs_code
        if parent_id is not None:
            data["parent_id"] = parent_id
        if default_btw_id is not None:
            data["default_btw_id"] = default_btw_id
        return parse_grootboekrekening(
            self._post(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen", json=data
            ),
            client=self._client,
        )

    def update(
        self,
        id: int,
        *,
        code: str | None = None,
        naam: str | None = None,
        rekening_type: RekeningType | None = None,
        categorie: RekeningCategorie | None = None,
        rgs_code: str | None = None,
        parent_id: int | None = None,
        default_btw_id: int | None = None,
        actief: bool | None = None,
    ) -> Grootboekrekening:
        """Partially update a grootboekrekening.

        Args:
            id: Grootboekrekening ID.
            code: New account code.
            naam: New account name.
            rekening_type: New account type.
            categorie: New statement category.
            rgs_code: New RGS code.
            parent_id: New parent account ID.
            default_btw_id: New default BTW code.
            actief: Enable or disable the account.
        """
        data: dict = {}
        if code is not None:
            data["code"] = code
        if naam is not None:
            data["naam"] = naam
        if rekening_type is not None:
            data["rekening_type"] = rekening_type.value
        if categorie is not None:
            data["categorie"] = categorie.value
        if rgs_code is not None:
            data["rgs_code"] = rgs_code
        if parent_id is not None:
            data["parent_id"] = parent_id
        if default_btw_id is not None:
            data["default_btw_id"] = default_btw_id
        if actief is not None:
            data["actief"] = actief
        return parse_grootboekrekening(
            self._patch(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}",
                json=data,
            ),
            client=self._client,
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

    def met_saldo(self, boekjaar_id: int) -> list[Grootboekrekening]:
        """Return all grootboekrekeningen enriched with transaction count and balance.

        Includes accounts with zero transactions in the boekjaar (with zeros).
        Useful for filtering the chart of accounts in scripts.

        Args:
            boekjaar_id: Fiscal year to aggregate over.

        Returns:
            One entry per rekening, sorted by code.
        """
        return [
            parse_grootboekrekening_met_saldo(
                d, client=self._client, boekjaar_id=boekjaar_id
            )
            for d in self._get(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/met-saldo/{boekjaar_id}"
            )
        ]

    def mutaties(self, id: int, boekjaar_id: int) -> list[GrootboekMutatie]:
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

    def find_by_naam(self, naam: str) -> Grootboekrekening | None:
        """Find a grootboekrekening by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact account name to search for (case-sensitive).

        Returns:
            The matching :py:class:`~mboek.models.grootboekrekeningen.Grootboekrekening`,
            or ``None`` if not found.
        """
        return next((r for r in self.list() if r.naam == naam), None)

    def find_by_code(self, code: str) -> Grootboekrekening | None:
        """Find a grootboekrekening by its account code.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            code: Account code to search for (e.g. ``"1220"``).

        Returns:
            The matching :py:class:`~mboek.models.grootboekrekeningen.Grootboekrekening`,
            or ``None`` if not found.
        """
        return next((r for r in self.list() if r.code == code), None)

    def clear_cache(self) -> None:
        """Remove the cached grootboekrekening list for this administratie.

        The next call to :py:meth:`list`, :py:meth:`find_by_naam`, or
        :py:meth:`find_by_code` will fetch fresh data from the API.
        """
        self._client._gbr_cache.pop(self._admin_id, None)
