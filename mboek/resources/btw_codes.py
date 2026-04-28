"""BTW codes resource."""

from __future__ import annotations

from mboek._parsers import parse_btw_code
from mboek.models.btw_codes import BtwCodeResponse, NewBtwCode, UpdateBtwCode
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

    def create(self, input: NewBtwCode) -> BtwCodeResponse:
        """Create a new BTW code.

        Args:
            input: BTW code parameters.
        """
        return parse_btw_code(
            self._post(
                f"/api/administraties/{self._admin_id}/btw-codes", json=input.to_dict()
            )
        )

    def update(self, id: int, input: UpdateBtwCode) -> BtwCodeResponse:
        """Partially update a BTW code.

        Args:
            id: BTW code ID.
            input: Fields to update.
        """
        return parse_btw_code(
            self._patch(
                f"/api/administraties/{self._admin_id}/btw-codes/{id}",
                json=input.to_dict(),
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
