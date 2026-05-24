"""Jaarrekening generation models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mboek.models._enums import JaarrekeningLogLevel


@dataclass(frozen=True)
class JaarrekeningBalansRegel:
    """A single beginbalans line returned by the jaarrekening runtime.

    Attributes:
        nummer: Account number.
        omschrijving: Human-readable description.
        bedrag: Amount in euros.
    """

    nummer: int
    omschrijving: str
    bedrag: Decimal


@dataclass(frozen=True)
class JaarrekeningBeginbalans:
    """Beginbalans data returned alongside a generated jaarrekening report.

    Attributes:
        jaar: Fiscal year of the beginbalans.
        regels: Beginbalans lines written to the report context.
        afrondingsverschil: Optional balancing line injected by the backend.
    """

    jaar: int
    regels: list[JaarrekeningBalansRegel]
    afrondingsverschil: JaarrekeningBalansRegel | None = None


@dataclass(frozen=True)
class JaarrekeningSummary:
    """Typed summary values returned by the jaarrekening runtime.

    Attributes:
        netto_resultaat: Net result after tax.
        vpb_resultaat_voor_belastingen: Result before corporate income tax.
        vpb_belastbaar_bedrag: Taxable amount for corporate income tax.
        vpb_berekend: Calculated corporate income tax.
        vpb_geboekt: Corporate income tax already booked.
    """

    netto_resultaat: Decimal
    vpb_resultaat_voor_belastingen: Decimal
    vpb_belastbaar_bedrag: Decimal
    vpb_berekend: Decimal
    vpb_geboekt: Decimal


@dataclass(frozen=True)
class JaarrekeningRuntimeMessage:
    """A runtime message emitted while generating a jaarrekening report.

    Attributes:
        level: Severity level reported by the backend.
        message: Human-readable message text.
    """

    level: JaarrekeningLogLevel
    message: str


@dataclass
class JaarrekeningHtmlReport:
    """Generated jaarrekening HTML report.

    Attributes:
        beginbalans: Beginbalans payload returned by the backend.
        summary: Typed summary values returned by the jaarrekening runtime.
        html: Generated HTML document.
        hash: Content hash of the generated report.
        messages: Runtime messages emitted during generation.
    """

    beginbalans: JaarrekeningBeginbalans
    summary: JaarrekeningSummary
    html: str
    hash: str
    messages: list[JaarrekeningRuntimeMessage]


@dataclass
class JaarrekeningPdfReport:
    """Generated jaarrekening PDF report.

    Attributes:
        beginbalans: Beginbalans payload returned by the backend.
        summary: Typed summary values returned by the jaarrekening runtime.
        hash: Content hash of the generated report.
        messages: Runtime messages emitted during generation.
        pdf: Decoded PDF bytes.
    """

    beginbalans: JaarrekeningBeginbalans
    summary: JaarrekeningSummary
    hash: str
    messages: list[JaarrekeningRuntimeMessage]
    pdf: bytes
