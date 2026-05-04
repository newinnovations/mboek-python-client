"""Grootboekrekeningen resource."""

from __future__ import annotations

import builtins

from mboek._parsers import (
    parse_grootboek_mutatie,
    parse_grootboekrekening,
    parse_grootboekrekening_met_saldo,
)
from mboek._unset import UNSET, UnsetType
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

    def list(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        code: str | None = None,
        refresh: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Grootboekrekening]:
        """Return grootboekrekeningen for the administratie.

        The full collection is cached on the client for the lifetime of the
        session (keyed by admin ID). Call ``list(refresh=True)`` or
        :py:meth:`clear_cache` to force a fresh fetch. All filters are exact
        matches and are combined with ``AND`` semantics. When ``limit`` and
        ``offset`` are omitted, all backend pages are fetched automatically
        before client-side filtering is applied.

        Args:
            refresh: When ``True``, bypass the cache and fetch from the API.
            limit: Maximum number of accounts to return from the filtered result.
            offset: Number of accounts to skip from the filtered result.

        Returns:
            List sorted by code ascending.
        """
        cache = self._client._gbr_cache
        filtered = id is not None or name is not None or code is not None
        use_full_collection = filtered or (limit is None and offset is None)

        if use_full_collection and not refresh and self._admin_id in cache:
            items = cache[self._admin_id]
        else:
            items = [
                parse_grootboekrekening(d, client=self._client)
                for d in self._get_paginated(
                    f"/api/administraties/{self._admin_id}/grootboekrekeningen",
                    limit=None if use_full_collection else limit,
                    offset=None if use_full_collection else offset,
                )
            ]
            if use_full_collection:
                cache[self._admin_id] = items

        if id is not None:
            items = [item for item in items if item.id == id]
        if name is not None:
            items = [item for item in items if item.naam == name]
        if code is not None:
            items = [item for item in items if item.code == code]
        if filtered:
            items = self._slice_items(items, limit=limit, offset=offset)
        return [item.copy() for item in items]

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
        response = self._post(
            f"/api/administraties/{self._admin_id}/grootboekrekeningen", json=data
        )
        self.clear_cache()
        return parse_grootboekrekening(
            response,
            client=self._client,
        )

    def update(
        self,
        id: int,
        *,
        code: str | None | UnsetType = UNSET,
        naam: str | None | UnsetType = UNSET,
        rekening_type: RekeningType | None | UnsetType = UNSET,
        categorie: RekeningCategorie | None | UnsetType = UNSET,
        rgs_code: str | None | UnsetType = UNSET,
        parent_id: int | None | UnsetType = UNSET,
        default_btw_id: int | None | UnsetType = UNSET,
        actief: bool | None | UnsetType = UNSET,
    ) -> Grootboekrekening:
        """Partially update a grootboekrekening.

        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

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
        self._set_patch_value(data, "code", code)
        self._set_patch_value(data, "naam", naam)
        self._set_patch_enum(data, "rekening_type", rekening_type)
        self._set_patch_enum(data, "categorie", categorie)
        self._set_patch_value(data, "rgs_code", rgs_code)
        self._set_patch_value(data, "parent_id", parent_id)
        self._set_patch_value(data, "default_btw_id", default_btw_id)
        self._set_patch_value(data, "actief", actief)
        response = self._patch(
            f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}",
            json=data,
        )
        self.clear_cache()
        return parse_grootboekrekening(
            response,
            client=self._client,
        )

    def delete(self, id: int) -> None:
        """Permanently delete a grootboekrekening.

        Fails if the account is referenced by existing boekingsregels or BTW codes.

        Args:
            id: Grootboekrekening ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}")
        self.clear_cache()

    def seed_rgs(self) -> None:
        """Seed the standard Dutch RGS (Referentie Grootboekschema) chart of accounts.

        Creates ~23 common account categories (1000–4900) if those codes do not
        already exist. Skips any code that is already present. Run
        :py:meth:`~mboek.resources.btw_codes.BtwCodesResource.seed_defaults`
        afterwards to set up linked BTW rekeningen.
        """
        self._post(f"/api/administraties/{self._admin_id}/grootboekrekeningen/seed-rgs")
        self.clear_cache()

    def met_saldo(
        self,
        boekjaar_id: int,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Grootboekrekening]:
        """Return all grootboekrekeningen enriched with transaction count and balance.

        Includes accounts with zero transactions in the boekjaar (with zeros).
        Useful for filtering the chart of accounts in scripts.

        Args:
            boekjaar_id: Fiscal year to aggregate over.
            limit: Maximum number of rekeningen to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of rekeningen to skip before collecting results.

        Returns:
            One entry per rekening, sorted by code.
        """
        return [
            parse_grootboekrekening_met_saldo(
                d, client=self._client, boekjaar_id=boekjaar_id
            )
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/met-saldo/{boekjaar_id}",
                limit=limit,
                offset=offset,
            )
        ]

    def mutaties(
        self,
        id: int,
        boekjaar_id: int,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[GrootboekMutatie]:
        """Return the full mutation ledger for a single rekening.

        Returns every boekingsregel with its date, dagboek, journal entry
        description, line description, and amount.

        Args:
            id: Grootboekrekening ID.
            boekjaar_id: Fiscal year to query.
            limit: Maximum number of mutaties to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of mutaties to skip before collecting results.

        Returns:
            List of mutations ordered by date and ID.
        """
        return [
            parse_grootboek_mutatie(d)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/grootboekrekeningen/{id}/mutaties",
                params={"boekjaar_id": boekjaar_id},
                limit=limit,
                offset=offset,
            )
        ]

    def clear_cache(self) -> None:
        """Remove the cached full grootboekrekening list for this administratie.

        The next call to :py:meth:`list` will fetch fresh data from the API.
        """
        self._client._gbr_cache.pop(self._admin_id, None)
