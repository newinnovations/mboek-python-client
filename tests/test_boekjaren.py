"""Tests for the boekjaren resource."""

from __future__ import annotations

import base64
import json
from datetime import date
from decimal import Decimal

import pytest
import responses

from mboek import JaarrekeningBeginbalans, JaarrekeningSummary
from mboek._exceptions import ConflictError, NotFoundError, ScopeError
from mboek.models._enums import BoekjaarStatus
from tests.conftest import (
    ADMINISTRATIE,
    BASE_URL,
    BOEKJAAR,
    DAGBOEK,
    GROOTBOEKREKENING,
)


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    items = client.administratie(1).boekjaren.list()
    assert len(items) == 1
    assert items[0].naam == "2024"
    assert items[0].status == BoekjaarStatus.OPEN
    boekjaar_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/administraties/1/boekjaren")
    ]
    assert "limit=1000" in boekjaar_calls[-1].request.url
    assert "offset=0" in boekjaar_calls[-1].request.url


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    item = client.administratie(1).boekjaren.get(10)
    assert item.id == 10
    assert item.start_datum == date(2024, 1, 1)


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren",
        json=BOEKJAAR,
        status=201,
    )
    item = client.administratie(1).boekjaren.create(
        naam="2024", start_datum=date(2024, 1, 1), eind_datum=date(2024, 12, 31)
    )
    assert item.naam == "2024"


def test_afsluiten(mocked_responses, client):
    gesloten = {**BOEKJAAR, "status": "gesloten"}
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/10/afsluiten",
        json=gesloten,
    )
    item = client.administratie(1).boekjaren.afsluiten(10)
    assert item.status == BoekjaarStatus.GESLOTEN


def test_afsluiten_already_closed(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/10/afsluiten",
        json={"error": "Already closed"},
        status=409,
    )
    with pytest.raises(ConflictError) as exc_info:
        client.administratie(1).boekjaren.afsluiten(10)
    assert exc_info.value.status_code == 409


def test_heropenen(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/10/heropenen",
        json=BOEKJAAR,
    )
    item = client.administratie(1).boekjaren.heropenen(10)
    assert item.status == BoekjaarStatus.OPEN


def test_set_huidig(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekjaren/10/set-huidig",
        json=BOEKJAAR,
    )
    item = client.administratie(1).boekjaren.set_huidig(10)
    assert item.id == 10


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1/boekjaren/10", status=204
    )
    client.administratie(1).boekjaren.delete(10)


def test_list_filters(mocked_responses, client):
    other = {**BOEKJAAR, "id": 11, "naam": "2025"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren",
        json=[BOEKJAAR, other],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren",
        json=[BOEKJAAR, other],
    )
    by_name = client.administratie(1).boekjaren.list(name="2024")
    assert len(by_name) == 1
    assert by_name[0].id == 10

    by_id = client.administratie(1).boekjaren.list(id=11)
    assert len(by_id) == 1
    assert by_id[0].naam == "2025"


def test_list_filters_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    assert client.administratie(1).boekjaren.list(name="2099") == []


def test_boekjaar_scope_by_id(mocked_responses, client):
    """Positional and keyword ID make one GET call and return a full Boekjaar."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    scope = client.administratie(1).boekjaar(10)
    assert scope.id == 10
    assert scope.naam == "2024"

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    scope = client.administratie(1).boekjaar(id=10)
    assert scope.id == 10


def test_boekjaar_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    scope = client.administratie(1).boekjaar(name="2024")
    assert scope.id == 10


def test_boekjaar_scope_by_name_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administratie(1).boekjaar(name="2099")
    assert "2099" in str(exc_info.value)


def test_boekjaar_scope_by_name_requires_single_match(mocked_responses, client):
    duplicate = {**BOEKJAAR, "id": 11}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren",
        json=[BOEKJAAR, duplicate],
    )
    with pytest.raises(ValueError, match="2024"):
        client.administratie(1).boekjaar(name="2024")


def test_boekjaar_scope_missing_args(client):
    with pytest.raises(ValueError):
        client.administratie(1).boekjaar()


def test_boekjaar_scope_ambiguous_args(client):
    with pytest.raises(ValueError):
        client.administratie(1).boekjaar(10, name="2024")


MET_SALDO = [{"rekening": GROOTBOEKREKENING, "aantal_transacties": 3, "saldo": 400000}]
JAARREKENING_SUMMARY = {
    "netto_resultaat": "460",
    "vpb_resultaat_voor_belastingen": "575",
    "vpb_belastbaar_bedrag": "575",
    "vpb_berekend": "115",
    "vpb_geboekt": "0",
}
JAARREKENING_BEGINBALANS = {
    "jaar": 2024,
    "regels": [{"nummer": 1200, "omschrijving": "Bank", "bedrag": "1250.50"}],
}
JAARREKENING_HTML_RESPONSE = {
    "beginbalans": JAARREKENING_BEGINBALANS,
    "summary": JAARREKENING_SUMMARY,
    "html": "<html><body>Atlas BV</body></html>",
    "hash": "0123456789abcdef",
    "messages": [{"level": "info", "message": "Report generated"}],
}
JAARREKENING_PDF_BYTES = b"%PDF-1.7\nboekjaar-convenience\n"
JAARREKENING_PDF_RESPONSE = {
    "beginbalans": JAARREKENING_BEGINBALANS,
    "summary": JAARREKENING_SUMMARY,
    "hash": "fedcba9876543210",
    "messages": [{"level": "warning", "message": "Using defaults"}],
    "pdf": base64.b64encode(JAARREKENING_PDF_BYTES).decode("ascii"),
}


def test_boekjaar_scope_grootboekrekeningen(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    items = client.administratie(1).boekjaar(10).grootboekrekeningen()
    assert len(items) == 1
    item = items[0]
    assert item.code == 1220
    assert item.naam == "Bank"
    assert item.transacties == 3
    from decimal import Decimal

    assert item.saldo == Decimal("4000.00")


def test_boekjaar_scope_grootboekrekening_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    item = client.administratie(1).boekjaar(10).grootboekrekening(code=1220)
    assert item.naam == "Bank"
    from decimal import Decimal

    assert item.saldo == Decimal("4000.00")


def test_boekjaar_scope_grootboekrekening_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administratie(1).boekjaar(10).grootboekrekening(code=9999)
    assert "9999" in str(exc_info.value)


def test_boekjaar_scope_dagboeken(mocked_responses, client):
    other = {
        **DAGBOEK,
        "id": 21,
        "code": "KAS",
        "naam": "Kasboek",
        "dagboek_type": "kas",
    }
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, other],
    )
    items = client.administratie(1).boekjaar(10).dagboeken(code="bank")
    assert len(items) == 1
    dagboek = items[0]
    assert dagboek.id == 20
    assert dagboek.naam == "Bankboek"
    assert dagboek._boekjaar_id == 10


def test_boekjaar_jaarrekening_html_derives_bedrijf_and_jaar(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1",
        json={**ADMINISTRATIE, "naam": "Atlas Holding BV"},
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/jaarrekening/html",
        json=JAARREKENING_HTML_RESPONSE,
    )

    report = client.administratie(1).boekjaar(10).jaarrekening_html()

    assert report.hash == "0123456789abcdef"
    assert isinstance(report.beginbalans, JaarrekeningBeginbalans)
    assert isinstance(report.summary, JaarrekeningSummary)
    assert report.summary.netto_resultaat == Decimal("460")
    assert report.beginbalans.regels[0].bedrag == Decimal("1250.50")
    assert report.html == "<html><body>Atlas BV</body></html>"

    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {
        "bedrijf": "atlasholding",
        "jaar": 2024,
        "debug": False,
        "minimal": False,
        "consolidatie": False,
        "write_beginbalans": False,
    }


def test_boekjaar_jaarrekening_pdf_uses_partial_shorthand_override(
    mocked_responses, client
):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/jaarrekening/pdf",
        json=JAARREKENING_PDF_RESPONSE,
    )

    report = (
        client.administratie(1)
        .boekjaar(10)
        .jaarrekening_pdf(
            bedrijf="atlas",
            debug=True,
            minimal=True,
        )
    )

    assert report.hash == "fedcba9876543210"
    assert report.summary.vpb_berekend == Decimal("115")
    assert report.pdf == JAARREKENING_PDF_BYTES

    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {
        "bedrijf": "atlas",
        "jaar": 2024,
        "debug": True,
        "minimal": True,
        "consolidatie": False,
        "write_beginbalans": False,
    }


# ── Scope error tests ──────────────────────────────────────────────────────────


def test_boekjaar_reports_scope_error():
    """Boekjaar without client raises ScopeError when accessing reports."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        _ = bj.reports


def test_boekjaar_btw_aangifte_scope_error():
    """Boekjaar without client raises ScopeError when accessing btw_aangifte."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        _ = bj.btw_aangifte


def test_boekjaar_grootboekrekeningen_scope_error():
    """Boekjaar without client raises ScopeError when calling grootboekrekeningen()."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        bj.grootboekrekeningen()


def test_boekjaar_dagboeken_scope_error():
    """Boekjaar without client raises ScopeError when calling dagboeken()."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        bj.dagboeken()


def test_boekjaar_jaarrekening_html_scope_error():
    """Boekjaar without client raises ScopeError when calling jaarrekening_html()."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        bj.jaarrekening_html()


def test_boekjaar_jaarrekening_pdf_scope_error():
    """Boekjaar without client raises ScopeError when calling jaarrekening_pdf()."""
    bj = client_free_boekjaar()
    with pytest.raises(ScopeError):
        bj.jaarrekening_pdf()


def test_boekjaar_dagboek_via_scope(mocked_responses, client):
    """boekjaar.dagboek(code=...) returns a Dagboek scoped to that boekjaar."""
    from mboek.models.dagboeken import Dagboek
    from tests.conftest import DAGBOEK

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    dagboek = client.administratie(1).boekjaar(10).dagboek(code="BANK")
    assert isinstance(dagboek, Dagboek)
    assert dagboek.id == 20
    assert dagboek._boekjaar_id == 10
    assert dagboek.naam == "Bankboek"


# ── Helpers ────────────────────────────────────────────────────────────────────


def client_free_boekjaar():
    """Return a Boekjaar instance without a client reference for scope-error tests."""
    from datetime import date, datetime

    from mboek.models._enums import BoekjaarStatus
    from mboek.models.boekjaren import Boekjaar

    return Boekjaar(
        id=10,
        administratie_id=1,
        naam="2024",
        start_datum=date(2024, 1, 1),
        eind_datum=date(2024, 12, 31),
        status=BoekjaarStatus.OPEN,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        client=None,
    )
