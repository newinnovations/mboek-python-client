"""Jaarrekening generation resource."""

from __future__ import annotations

from mboek._parsers import parse_jaarrekening_html, parse_jaarrekening_pdf
from mboek.models.jaarrekening import JaarrekeningHtmlReport, JaarrekeningPdfReport
from mboek.resources._base import BaseResource


def _normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _build_generate_payload(
    *,
    config_path: str | None,
    bedrijf: str | None,
    jaar: int | None,
    debug: bool,
    minimal: bool,
    consolidatie: bool,
    write_beginbalans: bool,
) -> dict[str, object]:
    normalized_config_path = _normalize_optional_text(
        config_path, field_name="config_path"
    )
    normalized_bedrijf = _normalize_optional_text(bedrijf, field_name="bedrijf")

    if normalized_config_path is not None:
        if normalized_bedrijf is not None or jaar is not None:
            raise ValueError("Provide either config_path or bedrijf + jaar")
    else:
        if normalized_bedrijf is None and jaar is None:
            raise ValueError("Provide config_path or bedrijf + jaar")
        if normalized_bedrijf is None or jaar is None:
            raise ValueError(
                "Provide both bedrijf and jaar when using shorthand config"
            )

    payload: dict[str, object] = {
        "debug": debug,
        "minimal": minimal,
        "consolidatie": consolidatie,
        "write_beginbalans": write_beginbalans,
    }
    if normalized_config_path is not None:
        payload["config_path"] = normalized_config_path
    else:
        payload["bedrijf"] = normalized_bedrijf
        payload["jaar"] = jaar
    return payload


class JaarrekeningResource(BaseResource):
    """Top-level jaarrekening HTML/PDF generation.

    Access via :py:attr:`MboekClient.jaarrekening`.
    """

    def generate_html(
        self,
        *,
        config_path: str | None = None,
        bedrijf: str | None = None,
        jaar: int | None = None,
        debug: bool = False,
        minimal: bool = False,
        consolidatie: bool = False,
        write_beginbalans: bool = False,
    ) -> JaarrekeningHtmlReport:
        """Generate a jaarrekening HTML report from a server-side config file.

        Provide either ``config_path`` or the shorthand combination
        ``bedrijf`` + ``jaar``.

        Returns:
            :py:class:`~mboek.models.jaarrekening.JaarrekeningHtmlReport`.
        """
        return parse_jaarrekening_html(
            self._post(
                "/api/jaarrekening/html",
                json=_build_generate_payload(
                    config_path=config_path,
                    bedrijf=bedrijf,
                    jaar=jaar,
                    debug=debug,
                    minimal=minimal,
                    consolidatie=consolidatie,
                    write_beginbalans=write_beginbalans,
                ),
            )
        )

    def generate_pdf(
        self,
        *,
        config_path: str | None = None,
        bedrijf: str | None = None,
        jaar: int | None = None,
        debug: bool = False,
        minimal: bool = False,
        consolidatie: bool = False,
        write_beginbalans: bool = False,
    ) -> JaarrekeningPdfReport:
        """Generate a jaarrekening PDF report from a server-side config file.

        Provide either ``config_path`` or the shorthand combination
        ``bedrijf`` + ``jaar``. The transport-level base64 payload is decoded to
        Python ``bytes``.

        Returns:
            :py:class:`~mboek.models.jaarrekening.JaarrekeningPdfReport`.
        """
        return parse_jaarrekening_pdf(
            self._post(
                "/api/jaarrekening/pdf",
                json=_build_generate_payload(
                    config_path=config_path,
                    bedrijf=bedrijf,
                    jaar=jaar,
                    debug=debug,
                    minimal=minimal,
                    consolidatie=consolidatie,
                    write_beginbalans=write_beginbalans,
                ),
            )
        )
