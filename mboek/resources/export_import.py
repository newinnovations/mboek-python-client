"""Export / import resource."""

from __future__ import annotations

import codecs
import re
from pathlib import Path
from typing import IO, Any

from mboek._parsers import (
    parse_administratie_export,
    parse_administratie_import_result,
    parse_boeking_export,
    parse_boekjaar_export,
    parse_boekjaar_import_result,
)
from mboek.models.export_import import (
    AdministratieExport,
    AdministratieImportResult,
    BoekingExport,
    BoekjaarExport,
    BoekjaarImportResult,
)
from mboek.resources._base import BaseResource

_XML_DECLARATION_ENCODING_RE = re.compile(
    r'^(?P<prefix>\s*<\?xml\b[^>]*?\bencoding\s*=\s*)(?P<quote>["\'])(?P<encoding>[^"\']+)(?P=quote)',
    re.IGNORECASE,
)


def _bool_query(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def _detect_xml_encoding(payload: bytes) -> str:
    if payload.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if payload.startswith(codecs.BOM_UTF32_LE):
        return "utf-32-le"
    if payload.startswith(codecs.BOM_UTF32_BE):
        return "utf-32-be"
    if payload.startswith(codecs.BOM_UTF16_LE):
        return "utf-16-le"
    if payload.startswith(codecs.BOM_UTF16_BE):
        return "utf-16-be"
    if payload.startswith(b"\x3c\x00\x00\x00\x3f\x00\x00\x00"):
        return "utf-32-le"
    if payload.startswith(b"\x00\x00\x00\x3c\x00\x00\x00\x3f"):
        return "utf-32-be"
    if payload.startswith(b"\x3c\x00\x3f\x00\x78\x00\x6d\x00"):
        return "utf-16-le"
    if payload.startswith(b"\x00\x3c\x00\x3f\x00\x78\x00\x6d"):
        return "utf-16-be"

    prefix = payload[:256].decode("ascii", errors="ignore")
    match = _XML_DECLARATION_ENCODING_RE.match(prefix)
    if match:
        return match.group("encoding")

    return "utf-8"


def _decode_xml_bytes(payload: bytes) -> str:
    encoding = _detect_xml_encoding(payload)
    try:
        return payload.decode(encoding)
    except LookupError as exc:
        raise ValueError(
            f"XML payload declares unsupported encoding {encoding!r}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"XML payload could not be decoded as {encoding!r}") from exc


def _normalize_xml_text(payload: str) -> str:
    payload = payload.removeprefix("\ufeff")
    return _XML_DECLARATION_ENCODING_RE.sub(
        lambda match: f'{match.group("prefix")}{match.group("quote")}UTF-8{match.group("quote")}',
        payload,
        count=1,
    )


def _read_xml_payload(source: Path | IO[str] | IO[bytes] | str | bytes) -> bytes:
    if isinstance(source, Path):
        payload: str | bytes = source.read_bytes()
    elif isinstance(source, str):
        if source.lstrip().startswith("<"):
            payload = source
        else:
            payload = Path(source).expanduser().read_bytes()
    elif isinstance(source, bytes):
        payload = source
    else:
        payload = source.read()
        if not isinstance(payload, (str, bytes)):
            raise TypeError("XML source must provide str or bytes data")

    if isinstance(payload, bytes):
        payload = _decode_xml_bytes(payload)
    return _normalize_xml_text(payload).encode("utf-8")


def _require_xml_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    raise TypeError("Expected XML response body")


class ExportImportResource(BaseResource):
    """Top-level export / import operations that do not require an administratie scope.

    Access via :py:attr:`MboekClient.export_import`.
    """

    def import_administratie(
        self, payload: AdministratieExport, *, overwrite: bool | None = None
    ) -> AdministratieImportResult:
        """Create a new administratie from a previously exported payload.

        Args:
            payload: Export payload obtained from
                :py:meth:`~mboek.resources.export_import.AdminExportImportResource.export_administratie`
                or loaded from JSON with
                :py:meth:`~mboek.models.export_import.AdministratieExport.from_dict`.
            overwrite: Replace an existing administratie with the same name.

        Returns:
            :py:class:`~mboek.models.export_import.AdministratieImportResult`.
        """
        return parse_administratie_import_result(
            self._post(
                "/api/administraties/import",
                json=payload.to_dict(),
                params={"overwrite": _bool_query(overwrite)},
            )
        )

    def import_administratie_xaf(
        self,
        source: Path | IO[str] | IO[bytes] | str | bytes,
        *,
        overwrite: bool | None = None,
        create_missing: bool | None = None,
        include_btw_codes: bool | None = None,
    ) -> AdministratieImportResult:
        """Create a new administratie from an Auditfile Financieel (XAF) export.

        Args:
            source: Path, path string, file object, XML string, or XML bytes to
                upload. String values that do not start with ``"<"`` are treated
                as filesystem paths. Non-UTF-8 XML is re-encoded to UTF-8 before
                sending.
            overwrite: Replace an existing administratie with the same name.
            create_missing: Synthesize missing grootboekrekeningen and BTW codes
                referenced by the XAF file.
            include_btw_codes: Import BTW codes from the XAF file when present.

        Returns:
            :py:class:`~mboek.models.export_import.AdministratieImportResult`.
        """
        return parse_administratie_import_result(
            self._post(
                "/api/administraties/import/xaf",
                params={
                    "overwrite": _bool_query(overwrite),
                    "create_missing": _bool_query(create_missing),
                    "include_btw_codes": _bool_query(include_btw_codes),
                },
                data=_read_xml_payload(source),
                headers={
                    "Content-Type": "application/xml",
                    "Accept": "application/json",
                },
            )
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

    def export_administratie(self) -> AdministratieExport:
        """Export the complete administratie as a typed JSON payload.

        Includes: BTW codes, grootboekrekeningen, dagboeken, auto-booking rules,
        boekjaren and all boekingen with their regels.

        Returns:
            :py:class:`~mboek.models.export_import.AdministratieExport`.
        """
        return parse_administratie_export(
            self._get(f"/api/administraties/{self._admin_id}/export")
        )

    def export_administratie_xaf(self) -> str:
        """Export the complete administratie as an Auditfile Financieel (XAF) XML document."""
        return _require_xml_text(
            self._get(f"/api/administraties/{self._admin_id}/export/xaf")
        )

    def export_boekjaar(self, boekjaar_id: int) -> BoekjaarExport:
        """Export a single boekjaar as a typed JSON payload.

        References are encoded by code rather than database ID so the export
        can be imported into an administratie with different IDs.

        Args:
            boekjaar_id: Boekjaar ID.

        Returns:
            :py:class:`~mboek.models.export_import.BoekjaarExport`.
        """
        return parse_boekjaar_export(
            self._get(
                f"/api/administraties/{self._admin_id}/boekjaren/{boekjaar_id}/export"
            )
        )

    def export_boekjaar_xaf(self, boekjaar_id: int) -> str:
        """Export a single boekjaar as an Auditfile Financieel (XAF) XML document."""
        return _require_xml_text(
            self._get(
                f"/api/administraties/{self._admin_id}/boekjaren/{boekjaar_id}/export/xaf"
            )
        )

    def export_boeking(self, boeking_id: int) -> BoekingExport:
        """Export a single boeking as a typed JSON payload.

        Args:
            boeking_id: Boeking ID.

        Returns:
            :py:class:`~mboek.models.export_import.BoekingExport`.
        """
        return parse_boeking_export(
            self._get(
                f"/api/administraties/{self._admin_id}/boekingen/{boeking_id}/export"
            )
        )

    def import_boekjaar(self, payload: BoekjaarExport) -> BoekjaarImportResult:
        """Import a boekjaar into the administratie.

        Codes are resolved against the administratie's existing configuration.

        Args:
            payload: Export payload obtained from :py:meth:`export_boekjaar`
                or loaded from JSON with
                :py:meth:`~mboek.models.export_import.BoekjaarExport.from_dict`.

        Returns:
            :py:class:`~mboek.models.export_import.BoekjaarImportResult`.
        """
        return parse_boekjaar_import_result(
            self._post(
                f"/api/administraties/{self._admin_id}/boekjaren/import",
                json=payload.to_dict(),
            )
        )

    def import_boekjaar_xaf(
        self,
        source: Path | IO[str] | IO[bytes] | str | bytes,
        *,
        create_missing: bool | None = None,
        include_btw_codes: bool | None = None,
    ) -> BoekjaarImportResult:
        """Import a boekjaar XAF file into the administratie.

        Args:
            source: Path, path string, file object, XML string, or XML bytes to
                upload. String values that do not start with ``"<"`` are treated
                as filesystem paths. Non-UTF-8 XML is re-encoded to UTF-8 before
                sending.
            create_missing: Create missing dagboeken, grootboekrekeningen, and
                BTW codes before importing the boekjaar.
            include_btw_codes: Import BTW codes from the XAF file when present.

        Returns:
            :py:class:`~mboek.models.export_import.BoekjaarImportResult`.
        """
        result = parse_boekjaar_import_result(
            self._post(
                f"/api/administraties/{self._admin_id}/boekjaren/import/xaf",
                params={
                    "create_missing": _bool_query(create_missing),
                    "include_btw_codes": _bool_query(include_btw_codes),
                },
                data=_read_xml_payload(source),
                headers={
                    "Content-Type": "application/xml",
                    "Accept": "application/json",
                },
            )
        )
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        GrootboekrekeningenResource(self._client, self._admin_id).clear_cache()
        return result
