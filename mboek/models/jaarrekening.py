"""Jaarrekening generation models."""

from __future__ import annotations

from dataclasses import dataclass

from mboek.models._enums import JaarrekeningLogLevel


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
        summary: Flattened summary values returned by the jaarrekening runtime.
        html: Generated HTML document.
        hash: Content hash of the generated report.
        messages: Runtime messages emitted during generation.
    """

    summary: dict[str, str]
    html: str
    hash: str
    messages: list[JaarrekeningRuntimeMessage]


@dataclass
class JaarrekeningPdfReport:
    """Generated jaarrekening PDF report.

    Attributes:
        summary: Flattened summary values returned by the jaarrekening runtime.
        hash: Content hash of the generated report.
        messages: Runtime messages emitted during generation.
        pdf: Decoded PDF bytes.
    """

    summary: dict[str, str]
    hash: str
    messages: list[JaarrekeningRuntimeMessage]
    pdf: bytes
