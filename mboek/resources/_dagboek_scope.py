"""DagboekScope — year-agnostic dagboek-level operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekingen import BoekingMetRegelsResponse
    from mboek.models.export_import import MatchSuggestion


class DagboekScope:
    """Year-agnostic operations scoped to a single dagboek.

    Obtain via :py:meth:`~mboek.resources._admin_scope.AdministratieScope.dagboek`::

        dagboek = client.administratie(1).dagboek(20)
        dagboek.rerun_regels()

    For boekingen (list/create), use the boekjaar-scoped access instead::

        bj_dagboek = client.administratie(1).boekjaar(10).dagboek(20)
        entries = bj_dagboek.boekingen.list()

    No HTTP call is made when creating this object.
    """

    def __init__(self, client: "MboekClient", admin_id: int, dagboek_id: int) -> None:
        self._client = client
        self._admin_id = admin_id
        self._dagboek_id = dagboek_id

    def rerun_regels(self) -> list["BoekingMetRegelsResponse"]:
        """Re-apply all active auto-booking rules to unprocessed boekingen in this dagboek.

        Unprocessed boekingen are those that still have the bankimport staging
        account (9990) as their contra account.

        Returns:
            The boekingen that were updated by this run.
        """
        from mboek._parsers import parse_boeking_met_regels

        data = self._client._request(
            "POST",
            f"/api/administraties/{self._admin_id}/dagboeken/{self._dagboek_id}/rerun-regels",
        )
        if isinstance(data, list):
            return [parse_boeking_met_regels(d) for d in data]
        return []

    def suggest(self, boeking_id: int) -> list["MatchSuggestion"]:
        """Get contra-account suggestions for an unprocessed boeking.

        The suggestion engine looks at previous bookings from the same
        counterparty to propose the most likely contra account.

        Args:
            boeking_id: Boeking ID to get suggestions for.

        Returns:
            List of :py:class:`~mboek.models.export_import.MatchSuggestion`
            objects ordered by confidence descending.
        """
        from mboek._parsers import parse_match_suggestion

        data = self._client._request(
            "POST",
            f"/api/administraties/{self._admin_id}/dagboeken/{self._dagboek_id}/suggest",
            json={"boeking_id": boeking_id},
        )
        if isinstance(data, list):
            return [parse_match_suggestion(d) for d in data]
        return []

    def import_boekingen(
        self, boekingen: list[dict]
    ) -> list["BoekingMetRegelsResponse"]:
        """Import a list of exported boekingen into this dagboek.

        Useful for copying boekingen from one instance or boekjaar to another.

        Args:
            boekingen: List of boeking payloads (from
                :py:meth:`~mboek.resources.export_import.AdminExportImportResource.export_boeking`).

        Returns:
            List of newly created boekingen.
        """
        from mboek._parsers import parse_boeking_met_regels

        data = self._client._request(
            "POST",
            f"/api/administraties/{self._admin_id}/dagboeken/{self._dagboek_id}/boekingen/import",
            json=boekingen,
        )
        if isinstance(data, list):
            return [parse_boeking_met_regels(d) for d in data]
        return []
