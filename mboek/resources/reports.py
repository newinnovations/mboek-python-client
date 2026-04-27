"""Reports resource."""

from __future__ import annotations

from mboek._parsers import parse_balans, parse_winst_verlies
from mboek.models.reports import BalansReport, WinstVerliesReport
from mboek.resources._base import BaseResource


class ReportsResource(BaseResource):
    """Financial report generation.

    Instantiated via :py:meth:`BoekjaarScope.reports`.
    """

    def __init__(self, client, admin_id: int, boekjaar_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id
        self._boekjaar_id = boekjaar_id

    def balans(self) -> BalansReport:
        """Generate a balance sheet (balans) for the fiscal year.

        Aggregates all boekingsregels for active activa and passiva
        grootboekrekeningen. Returns per-account debet/credit/saldo values
        and overall totals. ``in_balans`` is ``True`` when the difference
        between activa and passiva is less than €0.01.

        Returns:
            :py:class:`~mboek.models.reports.BalansReport`.
        """
        return parse_balans(
            self._get(
                f"/api/administraties/{self._admin_id}/rapporten/balans",
                params={"boekjaar_id": self._boekjaar_id},
            )
        )

    def winst_verlies(self) -> WinstVerliesReport:
        """Generate a profit-and-loss report (winst & verlies) for the fiscal year.

        Aggregates all boekingsregels for active kosten, opbrengsten and
        bijzonder grootboekrekeningen. Accounts with zero balance are omitted.

        Returns:
            :py:class:`~mboek.models.reports.WinstVerliesReport`.
        """
        return parse_winst_verlies(
            self._get(
                f"/api/administraties/{self._admin_id}/rapporten/winst-verlies",
                params={"boekjaar_id": self._boekjaar_id},
            )
        )
