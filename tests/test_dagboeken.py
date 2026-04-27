"""Tests for the dagboeken resource."""

from __future__ import annotations

import responses

from mboek import CreateDagboekInput
from mboek.models._enums import DagboekType
from tests.conftest import BASE_URL, DAGBOEK


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    items = client.administratie(1).dagboeken.list()
    assert len(items) == 1
    assert items[0].code == "BANK"
    assert items[0].dagboek_type == DagboekType.BANK


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    item = client.administratie(1).dagboeken.get(20)
    assert item.naam == "Bankboek"


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/administraties/1/dagboeken", json=DAGBOEK, status=201
    )
    inp = CreateDagboekInput(code="BANK", naam="Bankboek", dagboek_type=DagboekType.BANK)
    item = client.administratie(1).dagboeken.create(inp)
    assert item.id == 20


def test_werkstatus(mocked_responses, client):
    ws = [{"dagboek_id": 20, "onverwerkt": 3, "te_bevestigen": 1}]
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/werkstatus", json=ws
    )
    items = client.administratie(1).dagboeken.werkstatus(boekjaar_id=10)
    assert items[0].dagboek_id == 20
    assert items[0].onverwerkt == 3


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1/dagboeken/20", status=204
    )
    client.administratie(1).dagboeken.delete(20)


def test_find_by_naam_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_naam("Bankboek")
    assert result is not None
    assert result.id == 20


def test_find_by_naam_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_naam("Onbekend")
    assert result is None


def test_find_by_code_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_code("bank")  # case-insensitive
    assert result is not None
    assert result.code == "BANK"


def test_find_by_code_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_code("KAS")
    assert result is None
