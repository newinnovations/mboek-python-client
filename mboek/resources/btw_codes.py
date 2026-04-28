"""BTW codes resource."""

from __future__ import annotations

from decimal import Decimal

from mboek._parsers import parse_btw_code
from mboek.models._enums import BtwSoort
from mboek.models.btw_codes import BtwCodeResponse
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

    def list(self) -> list[BtwCodeResponse]:
        """Return all BTW codes for the administratie.

        Returns:
            List sorted by code ascending.
        """
        return [
            parse_btw_code(d)
            for d in self._get(f"/api/administraties/{self._admin_id}/btw-codes")
        ]

    def get(self, id: int) -> BtwCodeResponse:
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
    ) -> BtwCodeResponse:
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
        code: str | None = None,
        omschrijving: str | None = None,
        percentage: Decimal | None = None,
        soort: BtwSoort | None = None,
        output_rekening_id: int | None = None,
        input_rekening_id: int | None = None,
        pct_aftrek: Decimal | None = None,
        actief: bool | None = None,
    ) -> BtwCodeResponse:
        """Partially update a BTW code.

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
        if code is not None:
            data["code"] = code
        if omschrijving is not None:
            data["omschrijving"] = omschrijving
        if percentage is not None:
            data["percentage"] = str(percentage)
        if soort is not None:
            data["soort"] = soort.value
        if output_rekening_id is not None:
            data["output_rekening_id"] = output_rekening_id
        if input_rekening_id is not None:
            data["input_rekening_id"] = input_rekening_id
        if pct_aftrek is not None:
            data["pct_aftrek"] = str(pct_aftrek)
        if actief is not None:
            data["actief"] = actief
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

    def find_by_code(self, code: str) -> BtwCodeResponse | None:
        """Find a BTW code by its short code string.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            code: BTW code to search for (e.g. ``"V21"``).
                The comparison is case-insensitive.

        Returns:
            The matching :py:class:`~mboek.models.btw_codes.BtwCodeResponse`,
            or ``None`` if not found.
        """
        code_upper = code.upper()
        return next((b for b in self.list() if b.code.upper() == code_upper), None)
