"""Tests for BTW-aangifte parsing."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
import responses

from mboek import BtwAangifteStatus
from mboek._exceptions import MboekError
from tests.conftest import BASE_URL, BOEKJAAR

BTW_AANGIFTE = {
    "id": 80,
    "administratie_id": 1,
    "boekjaar_id": 10,
    "kwartaal": 1,
    "periode_start": "2024-01-01",
    "periode_eind": "2024-03-31",
    "berekening": {
        "r1a": {"grondslag": "100.00", "btw": "21.00"},
        "r1b": {"grondslag": "0.00", "btw": "0.00"},
        "r1c": {"grondslag": "0.00", "btw": "0.00"},
        "r1d": {"grondslag": "0.00", "btw": "0.00"},
        "r1e": {"grondslag": "0.00", "btw": "0.00"},
        "r2a": {"grondslag": "0.00", "btw": "0.00"},
        "r3a": {"grondslag": "0.00", "btw": "0.00"},
        "r3b": {"grondslag": "0.00", "btw": "0.00"},
        "r3c": {"grondslag": "0.00", "btw": "0.00"},
        "r4a": {"grondslag": "0.00", "btw": "0.00"},
        "r4b": {"grondslag": "0.00", "btw": "0.00"},
        "r5a": "21",
        "r5b": "0",
        "r5g": "21",
    },
    "r5g": "21",
    "status": "concept",
}


def test_list_parses_status_enum(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json=[BTW_AANGIFTE],
    )

    items = client.administratie(1).boekjaar(10).btw_aangifte.list()

    assert len(items) == 1
    assert items[0].status == BtwAangifteStatus.CONCEPT


def test_list_parses_berekening_fields(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json=[BTW_AANGIFTE],
    )

    item = client.administratie(1).boekjaar(10).btw_aangifte.list()[0]

    b = item.berekening
    assert b.r1a.grondslag == Decimal("100.00")
    assert b.r1a.btw == Decimal("21.00")
    assert b.r1b.grondslag == Decimal("0.00")
    assert b.r1b.btw == Decimal("0.00")
    assert b.r5a == Decimal("21")
    assert b.r5b == Decimal("0")
    assert b.r5g == Decimal("21")
    assert item.r5g == Decimal("21")


def test_list_parses_period_dates(mocked_responses, client):
    from datetime import date

    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json=[BTW_AANGIFTE],
    )

    item = client.administratie(1).boekjaar(10).btw_aangifte.list()[0]

    assert item.kwartaal == 1
    assert item.periode_start == date(2024, 1, 1)
    assert item.periode_eind == date(2024, 3, 31)
    assert item.administratie_id == 1
    assert item.boekjaar_id == 10


def test_berekenen_posts_payload_and_parses_response(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/btw-aangiften/berekenen",
        json=BTW_AANGIFTE,
    )

    item = client.administratie(1).boekjaar(10).btw_aangifte.berekenen(kwartaal=1)

    assert item.status == BtwAangifteStatus.CONCEPT
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"boekjaar_id": 10, "kwartaal": 1}


def test_vastleggen_parses_definitief_status(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/btw-aangiften/80/vastleggen",
        json={**BTW_AANGIFTE, "status": "definitief"},
    )

    item = client.administratie(1).boekjaar(10).btw_aangifte.vastleggen(80)

    assert item.status == BtwAangifteStatus.DEFINITIEF


def test_vastleggen_conflict(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/btw-aangiften/80/vastleggen",
        json={"error": "Boekjaar must be gesloten"},
        status=409,
    )

    with pytest.raises(MboekError) as exc_info:
        client.administratie(1).boekjaar(10).btw_aangifte.vastleggen(80)
    assert exc_info.value.status_code == 409


def test_delete_calls_endpoint(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.DELETE,
        f"{BASE_URL}/api/administraties/1/btw-aangiften/80",
        status=204,
    )

    client.administratie(1).boekjaar(10).btw_aangifte.delete(80)

    assert mocked_responses.calls[-1].request.url == (
        f"{BASE_URL}/api/administraties/1/btw-aangiften/80"
    )


def test_list_empty(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json=[],
    )

    items = client.administratie(1).boekjaar(10).btw_aangifte.list()

    assert items == []


def test_list_server_error(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json={"error": "Internal server error"},
        status=500,
    )

    with pytest.raises(MboekError) as exc_info:
        client.administratie(1).boekjaar(10).btw_aangifte.list()
    assert exc_info.value.status_code == 500


def test_list_unauthorized(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/btw-aangiften",
        json={"error": "Unauthorized"},
        status=401,
    )

    with pytest.raises(MboekError) as exc_info:
        client.administratie(1).boekjaar(10).btw_aangifte.list()
    assert exc_info.value.status_code == 401
