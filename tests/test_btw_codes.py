"""Tests for the BTW codes resource."""

from __future__ import annotations

from decimal import Decimal

import responses

from mboek.models._enums import BtwSoort
from tests.conftest import BASE_URL, BTW_CODE


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/btw-codes", json=[BTW_CODE]
    )
    items = client.administratie(1).btw_codes.list()
    assert len(items) == 1
    assert items[0].code == "V21"
    assert items[0].percentage == Decimal("21")
    assert items[0].pct_aftrek == Decimal("100")


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/btw-codes/50", json=BTW_CODE
    )
    item = client.administratie(1).btw_codes.get(50)
    assert item.soort == BtwSoort.VERKOPEN_NL_HOOG


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/btw-codes",
        json=BTW_CODE,
        status=201,
    )
    item = client.administratie(1).btw_codes.create(
        code="V21",
        omschrijving="Verkoop (21%)",
        percentage=Decimal("21"),
        soort=BtwSoort.VERKOPEN_NL_HOOG,
    )
    assert item.id == 50


def test_seed_defaults(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/btw-codes/seed-defaults",
        status=204,
    )
    client.administratie(1).btw_codes.seed_defaults()


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1/btw-codes/50", status=204
    )
    client.administratie(1).btw_codes.delete(50)


def test_list_filters(mocked_responses, client):
    other = {**BTW_CODE, "id": 51, "code": "V9"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-codes",
        json=[BTW_CODE, other],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-codes",
        json=[BTW_CODE, other],
    )
    by_code = client.administratie(1).btw_codes.list(code="v21")
    assert len(by_code) == 1
    assert by_code[0].id == 50

    by_id = client.administratie(1).btw_codes.list(id=51)
    assert len(by_id) == 1
    assert by_id[0].code == "V9"


def test_list_filters_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/btw-codes", json=[BTW_CODE]
    )
    assert client.administratie(1).btw_codes.list(code="V0") == []
