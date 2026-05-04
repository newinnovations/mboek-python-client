"""BTW codes resource."""

from __future__ import annotations

import builtins
from decimal import Decimal

from mboek._parsers import parse_btw_code
from mboek._unset import UNSET, UnsetType
from mboek.models._enums import BtwSoort
from mboek.models.btw_codes import BtwCode
from mboek.resources._base import BaseResource


class BtwCodesResource(BaseResource):
    """CRUD operations for BTW (VAT) codes.

    Instantiated via :py:meth:`AdministratieScope.btw_codes`.

    Standard Dutch codes created by :py:meth:`seed_defaults`:

    +---------+---------------------------+----------+
    | Code    | Description               | Rate     |
    +=========+===========================+==========+
    | V21     | Verkoop (21%)             | 21%      |
    | V9      | Verkoop (9%)              | 9%       |
    | V0      | Verkoop (0%)              | 0%       |
    | I21     | Inkoop (21%)              | 21%      |
    | I9      | Inkoop (9%)               | 9%       |
    | EU21    | Inkoop EU (21%)           | 21%      |
    | INT21   | Inkoop buiten EU (21%)    | 21%      |
    | VRL     | Verlegd NL (21%)          | 21%      |
    +---------+---------------------------+----------+
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(
        self,
        *,
        id: int | None = None,
        code: str | None = None,
        soort: BtwSoort | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[BtwCode]:
        """Return BTW codes for the administratie.

        All filters are exact matches and are combined with ``AND`` semantics.
        The ``code`` filter is case-insensitive.
        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically before client-side filtering is applied.

        Returns:
            List sorted by code ascending.
        """
        filtered = id is not None or code is not None or soort is not None
        items = [
            parse_btw_code(d)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/btw-codes",
                limit=None if filtered else limit,
                offset=None if filtered else offset,
            )
        ]
        if id is not None:
            items = [item for item in items if item.id == id]
        if code is not None:
            code_upper = code.upper()
            items = [item for item in items if item.code.upper() == code_upper]
        if soort is not None:
            items = [item for item in items if item.soort == soort]
        if filtered:
            return self._slice_items(items, limit=limit, offset=offset)
        return items

    def get(self, id: int) -> BtwCode:
        """Return a single BTW code.

        Args:
            id: BTW code ID.
        """
        return parse_btw_code(
            self._get(f"/api/administraties/{self._admin_id}/btw-codes/{id}")
        )

    def create(
        self,
        code: str,
        omschrijving: str,
        percentage: Decimal,
        soort: BtwSoort,
        *,
        output_rekening_id: int | None = None,
        input_rekening_id: int | None = None,
        pct_aftrek: Decimal | None = None,
    ) -> BtwCode:
        """Create a new BTW code.

        Args:
            code: Short code (must be unique within the administratie).
            omschrijving: Description.
            percentage: VAT rate as a percentage (e.g. ``Decimal("21")``).
            soort: VAT type.
            output_rekening_id: Linked "BTW te betalen" account.
            input_rekening_id: Linked "BTW te vorderen" account.
            pct_aftrek: Deductibility percentage (defaults to 100).
        """
        data: dict = {
            "code": code,
            "omschrijving": omschrijving,
            "percentage": str(percentage),
            "soort": soort.value,
        }
        if output_rekening_id is not None:
            data["output_rekening_id"] = output_rekening_id
        if input_rekening_id is not None:
            data["input_rekening_id"] = input_rekening_id
        if pct_aftrek is not None:
            data["pct_aftrek"] = str(pct_aftrek)
        return parse_btw_code(
            self._post(f"/api/administraties/{self._admin_id}/btw-codes", json=data)
        )

    def update(
        self,
        id: int,
        *,
        code: str | None | UnsetType = UNSET,
        omschrijving: str | None | UnsetType = UNSET,
        percentage: Decimal | None | UnsetType = UNSET,
        soort: BtwSoort | None | UnsetType = UNSET,
        output_rekening_id: int | None | UnsetType = UNSET,
        input_rekening_id: int | None | UnsetType = UNSET,
        pct_aftrek: Decimal | None | UnsetType = UNSET,
        actief: bool | None | UnsetType = UNSET,
    ) -> BtwCode:
        """Partially update a BTW code.

        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

        Args:
            id: BTW code ID.
            code: New short code.
            omschrijving: New description.
            percentage: New VAT rate.
            soort: New VAT type.
            output_rekening_id: New "BTW te betalen" account.
            input_rekening_id: New "BTW te vorderen" account.
            pct_aftrek: New deductibility percentage.
            actief: Enable or disable this code.
        """
        data: dict = {}
        self._set_patch_value(data, "code", code)
        self._set_patch_value(data, "omschrijving", omschrijving)
        self._set_patch_decimal(data, "percentage", percentage)
        self._set_patch_enum(data, "soort", soort)
        self._set_patch_value(data, "output_rekening_id", output_rekening_id)
        self._set_patch_value(data, "input_rekening_id", input_rekening_id)
        self._set_patch_decimal(data, "pct_aftrek", pct_aftrek)
        self._set_patch_value(data, "actief", actief)
        return parse_btw_code(
            self._patch(
                f"/api/administraties/{self._admin_id}/btw-codes/{id}", json=data
            )
        )

    def delete(self, id: int) -> None:
        """Permanently delete a BTW code.

        Args:
            id: BTW code ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/btw-codes/{id}")

    def seed_defaults(self) -> None:
        """Seed the standard Dutch BTW codes (V21, V9, V0, I21, I9, EU21, INT21, VRL).

        Skips codes that already exist. Output/input rekeningen are automatically
        resolved from grootboekrekeningen 2310 and 2320 if they exist (run
        :py:meth:`~mboek.resources.grootboekrekeningen.GrootboekrekeningenResource.seed_rgs`
        first).

        All seeded codes are created as **inactive** — activate them when
        appropriate for your business.
        """
        self._post(f"/api/administraties/{self._admin_id}/btw-codes/seed-defaults")
