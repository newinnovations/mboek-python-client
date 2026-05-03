"""Export / import resource."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any

from mboek.resources._base import BaseResource


def _bool_query(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def _read_xml_payload(source: Path | IO[str] | IO[bytes] | str | bytes) -> str | bytes:
    if isinstance(source, Path):
        return source.read_bytes()
    if isinstance(source, (str, bytes)):
        return source

    payload = source.read()
    if isinstance(payload, (str, bytes)):
        return payload
    raise TypeError("XML source must provide str or bytes data")


def _require_xml_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    raise TypeError("Expected XML response body")


class ExportImportResource(BaseResource):
    """Top-level export / import operations that do not require an administratie scope.

    Access via :py:attr:`MboekClient.export_import`.
    """

    def import_administratie(
        self, payload: dict, *, overwrite: bool | None = None
    ) -> dict:
        """Create a new administratie from a previously exported payload.

        Args:
            payload: Export payload obtained from
                :py:meth:`~mboek.resources.export_import.AdminExportImportResource.export_administratie`.
            overwrite: Replace an existing administratie with the same name.

        Returns:
            Summary dict with the new administratie ID and imported booking count.
        """
        return self._post(
            "/api/administraties/import",
            json=payload,
            params={"overwrite": _bool_query(overwrite)},
        )

    def import_administratie_xaf(
        self,
        source: Path | IO[str] | IO[bytes] | str | bytes,
        *,
        overwrite: bool | None = None,
        create_missing: bool | None = None,
    ) -> dict:
        """Create a new administratie from an Auditfile Financieel (XAF) export.

        Args:
            source: Path, file object, XML string, or XML bytes to upload.
            overwrite: Replace an existing administratie with the same name.
            create_missing: Synthesize missing grootboekrekeningen and BTW codes
                referenced by the XAF file.

        Returns:
            Summary dict with the new administratie ID and imported booking count.
        """
        return self._post(
            "/api/administraties/import/xaf",
            params={
                "overwrite": _bool_query(overwrite),
                "create_missing": _bool_query(create_missing),
            },
            data=_read_xml_payload(source),
            headers={
                "Content-Type": "application/xml",
                "Accept": "application/json",
            },
        )


class AdminExportImportResource(BaseResource):
    """Administratie-scoped export / import operations.

    Instantiated via :py:meth:`AdministratieScope.export_import`.

    JSON exports can be re-imported into any mBoek instance. XAF exports provide
    Auditfile Financieel interoperability for boekjaar-based exchange.
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

    def export_administratie_xaf(self) -> str:
        """Export the complete administratie as an Auditfile Financieel (XAF) XML document."""
        return _require_xml_text(
            self._get(f"/api/administraties/{self._admin_id}/export/xaf")
        )

    def export_boekjaar(self, boekjaar_id: int) -> dict:
        """Export a single boekjaar as a JSON-serialisable dict.

        References are encoded by code rather than database ID so the export
        can be imported into an administratie with different IDs.

        Args:
            boekjaar_id: Boekjaar ID.

        Returns:
            Export payload as a Python dict.
        """
        return self._get(
            f"/api/administraties/{self._admin_id}/boekjaren/{boekjaar_id}/export"
        )

    def export_boekjaar_xaf(self, boekjaar_id: int) -> str:
        """Export a single boekjaar as an Auditfile Financieel (XAF) XML document."""
        return _require_xml_text(
            self._get(
                f"/api/administraties/{self._admin_id}/boekjaren/{boekjaar_id}/export/xaf"
            )
        )

    def export_boeking(self, boeking_id: int) -> dict:
        """Export a single boeking as a JSON-serialisable dict.

        Args:
            boeking_id: Boeking ID.

        Returns:
            Export payload as a Python dict.
        """
        return self._get(
            f"/api/administraties/{self._admin_id}/boekingen/{boeking_id}/export"
        )

    def import_boekjaar(self, payload: dict) -> dict:
        """Import a boekjaar into the administratie.

        Codes are resolved against the administratie's existing configuration.

        Args:
            payload: Export payload obtained from :py:meth:`export_boekjaar`.

        Returns:
            Summary dict with the newly created boekjaar ID.
        """
        return self._post(
            f"/api/administraties/{self._admin_id}/boekjaren/import", json=payload
        )

    def import_boekjaar_xaf(
        self,
        source: Path | IO[str] | IO[bytes] | str | bytes,
        *,
        create_missing: bool | None = None,
    ) -> dict:
        """Import a boekjaar XAF file into the administratie.

        Args:
            source: Path, file object, XML string, or XML bytes to upload.
            create_missing: Create missing dagboeken, grootboekrekeningen, and
                BTW codes before importing the boekjaar.

        Returns:
            Summary dict with the new boekjaar ID and imported booking count.
        """
        return self._post(
            f"/api/administraties/{self._admin_id}/boekjaren/import/xaf",
            params={"create_missing": _bool_query(create_missing)},
            data=_read_xml_payload(source),
            headers={
                "Content-Type": "application/xml",
                "Accept": "application/json",
            },
        )
