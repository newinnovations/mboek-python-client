"""Tests for export/import resources."""

from __future__ import annotations

from io import StringIO

import responses

from tests.conftest import BASE_URL

ADMIN_IMPORT_RESULT = {
    "administratie_id": 7,
    "naam": "Imported BV",
    "boekingen_imported": 42,
}
BOEKJAAR_IMPORT_RESULT = {
    "boekjaar_id": 10,
    "naam": "2024",
    "boekingen_imported": 12,
}
XAF_XML = """<?xml version="1.0" encoding="UTF-8"?><AuditFileFinancial />"""


def _request_body(call) -> str:
    body = call.request.body
    if isinstance(body, bytes):
        return body.decode()
    if isinstance(body, str):
        return body
    raise TypeError("Expected request body to be text or bytes")


def test_import_administratie_supports_overwrite(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import",
        json=ADMIN_IMPORT_RESULT,
    )

    result = client.export_import.import_administratie(
        {"type": "administratie"}, overwrite=True
    )

    assert result["administratie_id"] == 7
    assert "overwrite=true" in mocked_responses.calls[-1].request.url


def test_import_administratie_xaf_from_path(tmp_path, mocked_responses, client):
    source = tmp_path / "administratie.xaf"
    source.write_text(XAF_XML, encoding="utf-8")
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import/xaf",
        json=ADMIN_IMPORT_RESULT,
    )

    result = client.export_import.import_administratie_xaf(
        source, overwrite=True, create_missing=False
    )

    call = mocked_responses.calls[-1]
    assert result["boekingen_imported"] == 42
    assert "overwrite=true" in call.request.url
    assert "create_missing=false" in call.request.url
    assert call.request.headers["Content-Type"] == "application/xml"
    assert call.request.headers["Accept"] == "application/json"
    assert _request_body(call) == XAF_XML


def test_export_administratie_xaf(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/export/xaf",
        body=XAF_XML,
        content_type="application/xml",
    )

    xml = client.administratie(1).export_import.export_administratie_xaf()

    assert xml == XAF_XML


def test_import_boekjaar_xaf_from_text_stream(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/import/xaf",
        json=BOEKJAAR_IMPORT_RESULT,
    )

    result = client.administratie(1).export_import.import_boekjaar_xaf(
        StringIO(XAF_XML), create_missing=True
    )

    call = mocked_responses.calls[-1]
    assert result["boekjaar_id"] == 10
    assert "create_missing=true" in call.request.url
    assert call.request.headers["Content-Type"] == "application/xml"
    assert _request_body(call) == XAF_XML


def test_export_boekjaar_xaf(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10/export/xaf",
        body=XAF_XML,
        content_type="application/xml",
    )

    xml = client.administratie(1).export_import.export_boekjaar_xaf(10)

    assert xml == XAF_XML
