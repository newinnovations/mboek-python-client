"""Tests for the boekjaren resource."""

from __future__ import annotations

import responses

from mboek import CreateBoekjaarInput
from mboek._exceptions import ConflictError, NotFoundError
from mboek.models._enums import BoekjaarStatus
from tests.conftest import BASE_URL, BOEKJAAR, GROOTBOEKREKENING

from datetime import date


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    items = client.administratie(1).boekjaren.list()
    assert len(items) == 1
    assert items[0].naam == "2024"
    assert items[0].status == BoekjaarStatus.OPEN


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
    inp = CreateBoekjaarInput(
        naam="2024", start_datum=date(2024, 1, 1), eind_datum=date(2024, 12, 31)
    )
    item = client.administratie(1).boekjaren.create(inp)
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
    try:
        client.administratie(1).boekjaren.afsluiten(10)
        assert False
    except ConflictError as e:
        assert e.status_code == 409


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


def test_find_by_naam_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    result = client.administratie(1).boekjaren.find_by_naam("2024")
    assert result is not None
    assert result.id == 10


def test_find_by_naam_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    result = client.administratie(1).boekjaren.find_by_naam("2099")
    assert result is None


def test_boekjaar_scope_by_id(client):
    """Positional and keyword ID still work without an HTTP call."""
    scope = client.administratie(1).boekjaar(10)
    assert scope.boekjaar_id == 10

    scope = client.administratie(1).boekjaar(boekjaar_id=10)
    assert scope.boekjaar_id == 10


def test_boekjaar_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    scope = client.administratie(1).boekjaar(name="2024")
    assert scope.boekjaar_id == 10


def test_boekjaar_scope_by_name_not_found(mocked_responses, client):
    from mboek._exceptions import NotFoundError

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren", json=[BOEKJAAR]
    )
    try:
        client.administratie(1).boekjaar(name="2099")
        assert False
    except NotFoundError as e:
        assert "2099" in str(e)


def test_boekjaar_scope_missing_args(client):
    try:
        client.administratie(1).boekjaar()
        assert False
    except ValueError:
        pass


def test_boekjaar_scope_ambiguous_args(client):
    try:
        client.administratie(1).boekjaar(10, name="2024")
        assert False
    except ValueError:
        pass


MET_SALDO = [{"rekening": GROOTBOEKREKENING, "aantal_transacties": 3, "saldo": 400000}]


def test_boekjaar_scope_grootboekrekeningen(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    items = client.administratie(1).boekjaar(10).grootboekrekeningen()
    assert len(items) == 1
    item = items[0]
    assert item.code == "1220"
    assert item.naam == "Bank"
    assert item.transacties == 3
    from decimal import Decimal

    assert item.saldo == Decimal("4000.00")


def test_boekjaar_scope_grootboekrekening_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    item = client.administratie(1).boekjaar(10).grootboekrekening(code="1220")
    assert item.naam == "Bank"
    from decimal import Decimal

    assert item.saldo == Decimal("4000.00")


def test_boekjaar_scope_grootboekrekening_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=MET_SALDO,
    )
    try:
        client.administratie(1).boekjaar(10).grootboekrekening(code="9999")
        assert False
    except NotFoundError as e:
        assert "9999" in str(e)
