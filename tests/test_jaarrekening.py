"""Tests for jaarrekening operations."""

from __future__ import annotations

import base64
import json
from decimal import Decimal

import pytest
import responses

from mboek import (
    JaarrekeningBalansRegel,
    JaarrekeningBeginbalans,
    JaarrekeningHtmlReport,
    JaarrekeningLogLevel,
    JaarrekeningPdfReport,
    JaarrekeningSummary,
)
from tests.conftest import BASE_URL

SUMMARY_RESPONSE = {
    "netto_resultaat": "460",
    "vpb_resultaat_voor_belastingen": "575",
    "vpb_belastbaar_bedrag": "575",
    "vpb_berekend": "115",
    "vpb_geboekt": "0",
}
BEGINBALANS_RESPONSE = {
    "jaar": 2025,
    "regels": [
        {"nummer": 1200, "omschrijving": "Bank", "bedrag": "1234.56"},
        {"nummer": 1600, "omschrijving": "Crediteuren", "bedrag": "-300.00"},
    ],
    "afrondingsverschil": {
        "nummer": 9998,
        "omschrijving": "Afrondingsverschil",
        "bedrag": "0.01",
    },
}
HTML_RESPONSE = {
    "beginbalans": BEGINBALANS_RESPONSE,
    "summary": SUMMARY_RESPONSE,
    "html": "<html><body>Atlas Holding B.V.</body></html>",
    "hash": "0123456789abcdef",
    "messages": [{"level": "info", "message": "Report generated"}],
}

PDF_BYTES = b"%PDF-1.7\nfake-pdf\n"
PDF_RESPONSE = {
    "beginbalans": BEGINBALANS_RESPONSE,
    "summary": SUMMARY_RESPONSE,
    "hash": "fedcba9876543210",
    "messages": [{"level": "warning", "message": "Used fallback stylesheet"}],
    "pdf": base64.b64encode(PDF_BYTES).decode("ascii"),
}


def test_generate_html_returns_typed_report(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/jaarrekening/html",
        json=HTML_RESPONSE,
    )

    report = client.jaarrekening.generate_html(
        config_path=" /srv/reports/holding-2025.yaml "
    )

    assert isinstance(report, JaarrekeningHtmlReport)
    assert isinstance(report.beginbalans, JaarrekeningBeginbalans)
    assert isinstance(report.summary, JaarrekeningSummary)
    assert report.summary.netto_resultaat == Decimal("460")
    assert report.summary.vpb_berekend == Decimal("115")
    assert len(report.beginbalans.regels) == 2
    assert isinstance(report.beginbalans.regels[0], JaarrekeningBalansRegel)
    assert report.beginbalans.regels[0].bedrag == Decimal("1234.56")
    assert report.beginbalans.afrondingsverschil is not None
    assert report.beginbalans.afrondingsverschil.bedrag == Decimal("0.01")
    assert report.html == "<html><body>Atlas Holding B.V.</body></html>"
    assert report.hash == "0123456789abcdef"
    assert len(report.messages) == 1
    assert report.messages[0].level == JaarrekeningLogLevel.INFO
    assert report.messages[0].message == "Report generated"

    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {
        "config_path": "/srv/reports/holding-2025.yaml",
        "debug": False,
        "minimal": False,
        "consolidatie": False,
        "write_beginbalans": False,
    }


def test_generate_pdf_decodes_pdf_bytes(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/jaarrekening/pdf",
        json=PDF_RESPONSE,
    )

    report = client.jaarrekening.generate_pdf(
        bedrijf="atlas-holding",
        jaar=2025,
        debug=True,
        minimal=True,
        consolidatie=True,
        write_beginbalans=True,
    )

    assert isinstance(report, JaarrekeningPdfReport)
    assert report.summary.netto_resultaat == Decimal("460")
    assert report.beginbalans.jaar == 2025
    assert report.hash == "fedcba9876543210"
    assert report.pdf == PDF_BYTES
    assert len(report.messages) == 1
    assert report.messages[0].level == JaarrekeningLogLevel.WARNING
    assert report.messages[0].message == "Used fallback stylesheet"

    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {
        "bedrijf": "atlas-holding",
        "jaar": 2025,
        "debug": True,
        "minimal": True,
        "consolidatie": True,
        "write_beginbalans": True,
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, r"Provide config_path or bedrijf \+ jaar"),
        ({"bedrijf": "atlas-holding"}, "Provide both bedrijf and jaar"),
        (
            {
                "config_path": "/srv/report.yaml",
                "bedrijf": "atlas-holding",
                "jaar": 2025,
            },
            r"Provide either config_path or bedrijf \+ jaar",
        ),
    ],
)
def test_generate_html_validates_config_selection(client, kwargs, message):
    with pytest.raises(ValueError, match=message):
        client.jaarrekening.generate_html(**kwargs)


def test_generate_pdf_rejects_invalid_base64(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/jaarrekening/pdf",
        json={
            "beginbalans": BEGINBALANS_RESPONSE,
            "summary": SUMMARY_RESPONSE,
            "hash": "fedcba9876543210",
            "messages": [],
            "pdf": "not-base64!!!",
        },
    )

    with pytest.raises(ValueError, match="valid base64"):
        client.jaarrekening.generate_pdf(config_path="/srv/reports/holding-2025.yaml")
