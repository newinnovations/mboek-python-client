"""Tests for export/import resources."""

from __future__ import annotations

from io import BytesIO, StringIO

import pytest
import responses

from mboek._exceptions import MboekError, NotFoundError, ValidationError
from tests.conftest import BASE_URL, GROOTBOEKREKENING

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
NON_UTF8_XAF_XML = """<?xml version="1.0" encoding="Windows-1252"?><AuditFileFinancial><Description>Bedrag € 12</Description></AuditFileFinancial>"""
NORMALIZED_XAF_XML = NON_UTF8_XAF_XML.replace(
    'encoding="Windows-1252"', 'encoding="UTF-8"'
)
BANK_IMPORT_RESULT = {
    "imported": 3,
    "duplicates_skipped": 1,
    "zero_bedrag_skipped": 2,
    "boekjaar_niet_gevonden_skipped": 0,
    "auto_geboekt": 2,
    "unmatched_ibans": ["NL00BANK0123456789"],
    "parse_warnings": ["Malformed line 42"],
}


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


def test_import_administratie_xaf_normalizes_non_utf8_path(
    tmp_path, mocked_responses, client
):
    source = tmp_path / "administratie.xaf"
    source.write_bytes(NON_UTF8_XAF_XML.encode("cp1252"))
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/import/xaf",
        json=ADMIN_IMPORT_RESULT,
    )

    client.export_import.import_administratie_xaf(source)

    call = mocked_responses.calls[-1]
    assert call.request.headers["Content-Type"] == "application/xml"
    assert _request_body(call) == NORMALIZED_XAF_XML


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


def test_import_boekjaar_xaf_normalizes_non_utf8_bytes_stream(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/import/xaf",
        json=BOEKJAAR_IMPORT_RESULT,
    )

    client.administratie(1).export_import.import_boekjaar_xaf(
        BytesIO(NON_UTF8_XAF_XML.encode("cp1252"))
    )

    call = mocked_responses.calls[-1]
    assert call.request.headers["Content-Type"] == "application/xml"
    assert _request_body(call) == NORMALIZED_XAF_XML


def test_bank_import_upload_supports_allow_duplicates_and_new_result_shape(
    tmp_path, mocked_responses, client
):
    source = tmp_path / "statement.940"
    source.write_bytes(b":20:START")
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/import",
        json=BANK_IMPORT_RESULT,
    )

    result = client.administratie(1).import_.upload(source, allow_duplicates=True)

    call = mocked_responses.calls[-1]
    body = _request_body(call)
    assert result.imported == 3
    assert result.duplicates_skipped == 1
    assert result.zero_bedrag_skipped == 2
    assert result.boekjaar_niet_gevonden_skipped == 0
    assert result.auto_geboekt == 2
    assert result.unmatched_ibans == ["NL00BANK0123456789"]
    assert result.parse_warnings == ["Malformed line 42"]
    assert 'name="allow_duplicates"' in body
    assert "true" in body


def test_bank_import_upload_file_object_omits_allow_duplicates_by_default(
    mocked_responses, client
):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/import",
        json={
            key: value
            for key, value in BANK_IMPORT_RESULT.items()
            if key != "parse_warnings"
        },
    )

    result = client.administratie(1).import_.upload(
        BytesIO(b":20:START"), filename="statement.940"
    )

    body = _request_body(mocked_responses.calls[-1])
    assert result.parse_warnings is None
    assert 'name="allow_duplicates"' not in body


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


def test_import_boekjaar_xaf_invalidates_grootboekrekening_cache(
    mocked_responses, client
):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/import/xaf",
        json=BOEKJAAR_IMPORT_RESULT,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )

    gbr = client.administratie(1).grootboekrekeningen
    gbr.list()
    client.administratie(1).export_import.import_boekjaar_xaf(
        XAF_XML, create_missing=True
    )
    gbr.list()

    gbr_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(
            f"{BASE_URL}/api/administraties/1/grootboekrekeningen"
        )
    ]
    assert len(gbr_calls) == 2
