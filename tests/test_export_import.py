"""Tests for export/import resources."""

from __future__ import annotations

from io import BytesIO, StringIO

import pytest
import responses

from mboek._exceptions import MboekError, NotFoundError, ValidationError
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


# ── Failure path tests ────────────────────────────────────────────────────────


def test_import_administratie_server_error(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import",
        json={"error": "Internal server error"},
        status=500,
    )
    with pytest.raises(MboekError) as exc_info:
        client.export_import.import_administratie({"type": "administratie"})
    assert exc_info.value.status_code == 500


def test_import_administratie_validation_error(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import",
        json={"error": "Validation failed"},
        status=422,
    )
    with pytest.raises(ValidationError) as exc_info:
        client.export_import.import_administratie({"type": "bad"})
    assert exc_info.value.status_code == 422


def test_import_administratie_xaf_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import/xaf",
        json={"error": "Not found"},
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.export_import.import_administratie_xaf(XAF_XML)


def test_import_administratie_xaf_from_bytes_stream(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import/xaf",
        json=ADMIN_IMPORT_RESULT,
    )
    result = client.export_import.import_administratie_xaf(
        BytesIO(XAF_XML.encode()), overwrite=False
    )
    call = mocked_responses.calls[-1]
    assert result["administratie_id"] == 7
    assert call.request.headers["Content-Type"] == "application/xml"
    assert _request_body(call) == XAF_XML


def test_import_administratie_xaf_overwrite_and_create_missing(
    mocked_responses, client
):
    """Both overwrite and create_missing can be set independently."""
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import/xaf",
        json=ADMIN_IMPORT_RESULT,
    )
    client.export_import.import_administratie_xaf(
        XAF_XML, overwrite=True, create_missing=True
    )
    url = mocked_responses.calls[-1].request.url
    assert "overwrite=true" in url
    assert "create_missing=true" in url


def test_export_administratie_xaf_server_error(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/export/xaf",
        json={"error": "Server error"},
        status=500,
    )
    with pytest.raises(MboekError) as exc_info:
        client.administratie(1).export_import.export_administratie_xaf()
    assert exc_info.value.status_code == 500


def test_export_boeking(mocked_responses, client):
    boeking_payload = {"id": 100, "type": "boeking", "regels": []}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekingen/100/export",
        json=boeking_payload,
    )
    result = client.administratie(1).export_import.export_boeking(100)
    assert result["id"] == 100


def test_import_boekjaar_xaf_validation_error(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/import/xaf",
        json={"error": "Validation failed"},
        status=422,
    )
    with pytest.raises(ValidationError):
        client.administratie(1).export_import.import_boekjaar_xaf(XAF_XML)
