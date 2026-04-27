"""Export / import resource."""

from __future__ import annotations

from mboek.resources._base import BaseResource


class ExportImportResource(BaseResource):
    """Top-level export / import operations that do not require an administratie scope.

    Access via :py:attr:`MboekClient.export_import`.
    """

    def import_administratie(self, payload: dict) -> dict:
        """Create a new administratie from a previously exported payload.

        Args:
            payload: Export payload obtained from
                :py:meth:`~mboek.resources.export_import.AdminExportImportResource.export_administratie`.

        Returns:
            Summary dict with the newly created administratie ID.
        """
        return self._post("/api/administraties/import", json=payload)


class AdminExportImportResource(BaseResource):
    """Administratie-scoped export / import operations.

    Instantiated via :py:meth:`AdministratieScope.export_import`.

    Exported files are JSON and can be re-imported into any mBoek instance.
    The export includes all configuration (BTW codes, grootboekrekeningen,
    dagboeken, auto-booking rules) and all boekingen.
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def export_administratie(self) -> dict:
        """Export the complete administratie as a JSON-serialisable dict.

        Includes: BTW codes, grootboekrekeningen, dagboeken, auto-booking rules,
        boekjaren and all boekingen with their regels.

        Returns:
            Export payload as a Python dict (can be ``json.dump``'d to a file).
        """
        return self._get(f"/api/administraties/{self._admin_id}/export")

    def export_boekjaar(self, boekjaar_id: int) -> dict:
        """Export a single boekjaar as a JSON-serialisable dict.

        References are encoded by code rather than database ID so the export
        can be imported into an administratie with different IDs.

        Args:
            boekjaar_id: Boekjaar ID.

        Returns:
            Export payload as a Python dict.
        """
        return self._get(f"/api/administraties/{self._admin_id}/boekjaren/{boekjaar_id}/export")

    def export_boeking(self, boeking_id: int) -> dict:
        """Export a single boeking as a JSON-serialisable dict.

        Args:
            boeking_id: Boeking ID.

        Returns:
            Export payload as a Python dict.
        """
        return self._get(f"/api/administraties/{self._admin_id}/boekingen/{boeking_id}/export")

    def import_boekjaar(self, payload: dict) -> dict:
        """Import a boekjaar into the administratie.

        Codes are resolved against the administratie's existing configuration.

        Args:
            payload: Export payload obtained from :py:meth:`export_boekjaar`.

        Returns:
            Summary dict with the newly created boekjaar ID.
        """
        return self._post(f"/api/administraties/{self._admin_id}/boekjaren/import", json=payload)
