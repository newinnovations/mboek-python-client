"""Tests for jaarrekening operations."""

from __future__ import annotations

import base64
import json

import pytest
import responses

from mboek import (
    JaarrekeningHtmlReport,
    JaarrekeningLogLevel,
    JaarrekeningPdfReport,
)
from tests.conftest import BASE_URL

HTML_RESPONSE = {
    "summary": {"netto_resultaat": "460", "boekjaar": "2025"},
    "html": "<html><body>Atlas Holding B.V.</body></html>",
    "hash": "0123456789abcdef",
    "messages": [{"level": "info", "message": "Report generated"}],
}

PDF_BYTES = b"%PDF-1.7\nfake-pdf\n"
PDF_RESPONSE = {
    "summary": {"netto_resultaat": "460"},
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
    assert report.summary == {"netto_resultaat": "460", "boekjaar": "2025"}
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
    assert report.summary == {"netto_resultaat": "460"}
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
            {"config_path": "/srv/report.yaml", "bedrijf": "atlas-holding", "jaar": 2025},
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
            "summary": {"netto_resultaat": "460"},
            "hash": "fedcba9876543210",
            "messages": [],
            "pdf": "not-base64!!!",
        },
    )

    with pytest.raises(ValueError, match="valid base64"):
        client.jaarrekening.generate_pdf(config_path="/srv/reports/holding-2025.yaml")
