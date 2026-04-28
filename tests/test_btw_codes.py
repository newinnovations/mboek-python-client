"""Tests for the BTW codes resource."""

from __future__ import annotations

import responses

from mboek import CreateBtwCodeInput
from mboek.models._enums import BtwSoort
from decimal import Decimal
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
    inp = CreateBtwCodeInput(
        code="V21",
        omschrijving="Verkoop (21%)",
        percentage=Decimal("21"),
        soort=BtwSoort.VERKOPEN_NL_HOOG,
    )
    item = client.administratie(1).btw_codes.create(inp)
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


def test_find_by_code_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/btw-codes", json=[BTW_CODE]
    )
    result = client.administratie(1).btw_codes.find_by_code("v21")  # case-insensitive
    assert result is not None
    assert result.id == 50


def test_find_by_code_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/btw-codes", json=[BTW_CODE]
    )
    result = client.administratie(1).btw_codes.find_by_code("V0")
    assert result is None
