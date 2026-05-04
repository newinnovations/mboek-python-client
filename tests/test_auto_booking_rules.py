"""Tests for the automatic booking rules resource."""

from __future__ import annotations

import json

import pytest
import responses

from mboek import AutoBookingActieType, NewAutoBookingRuleLine
from mboek._exceptions import MboekError, NotFoundError
from mboek.models._enums import AutoBookingBedragType
from tests.conftest import BASE_URL, GROOTBOEKREKENING

AUTO_BOOKING_RULE = {
    "id": 70,
    "administratie_id": 1,
    "naam": "Bank costs",
    "prioriteit": 10,
    "actief": True,
    "actie_type": "enkel",
    "btw_code_id": None,
    "iban_eigen": None,
    "iban_tegenpartij": None,
    "omschrijving_regex": "KOSTEN",
    "tegenrekening_id": 30,
    "lines": [
        {
            "id": 1,
            "rule_id": 70,
            "volgorde": 1,
            "tegenrekening_id": 30,
            "btw_code_id": None,
            "omschrijving": "Bank costs",
            "bedrag_type": "rest",
            "bedrag": None,
        }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


def test_list_limit_offset(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels",
        json=[AUTO_BOOKING_RULE],
    )

    items = client.administratie(1).auto_booking_rules.list(limit=10, offset=20)

    assert len(items) == 1
    assert items[0].actie_type == AutoBookingActieType.ENKEL
    rule_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/administraties/1/regels")
    ]
    assert "limit=10" in rule_calls[-1].request.url
    assert "offset=20" in rule_calls[-1].request.url


def test_list_empty(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels",
        json=[],
    )
    items = client.administratie(1).auto_booking_rules.list()
    assert items == []


def test_list_parses_all_fields(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels",
        json=[AUTO_BOOKING_RULE],
    )
    rule = client.administratie(1).auto_booking_rules.list()[0]
    assert rule.id == 70
    assert rule.naam == "Bank costs"
    assert rule.prioriteit == 10
    assert rule.actief is True
    assert rule.actie_type == AutoBookingActieType.ENKEL
    assert rule.omschrijving_regex == "KOSTEN"
    assert rule.iban_eigen is None
    assert rule.iban_tegenpartij is None
    assert rule.tegenrekening_id == 30
    assert len(rule.lines) == 1
    line = rule.lines[0]
    assert line.tegenrekening_id == 30
    assert line.bedrag_type == AutoBookingBedragType.REST
    assert line.bedrag is None


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/regels",
        json=AUTO_BOOKING_RULE,
        status=201,
    )
    line = NewAutoBookingRuleLine(
        tegenrekening_id=30, bedrag_type=AutoBookingBedragType.REST
    )
    rule = client.administratie(1).auto_booking_rules.create(
        naam="Bank costs",
        actie_type=AutoBookingActieType.ENKEL,
        lines=[line],
        prioriteit=10,
        omschrijving_regex="KOSTEN",
    )
    assert rule.id == 70
    assert rule.naam == "Bank costs"
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["naam"] == "Bank costs"
    assert body["actie_type"] == "enkel"
    assert body["prioriteit"] == 10
    assert body["omschrijving_regex"] == "KOSTEN"
    assert body["lines"][0]["tegenrekening_id"] == 30


def test_create_with_rekening_naam_resolves_id(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/regels",
        json=AUTO_BOOKING_RULE,
        status=201,
    )
    line = NewAutoBookingRuleLine(
        tegenrekening_naam="Bank", bedrag_type=AutoBookingBedragType.REST
    )
    rule = client.administratie(1).auto_booking_rules.create(
        naam="Bank costs",
        actie_type=AutoBookingActieType.ENKEL,
        lines=[line],
    )
    assert rule.id == 70
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["lines"][0]["tegenrekening_id"] == 30


def test_create_simple_enkel_rule_without_lines(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/regels",
        json=AUTO_BOOKING_RULE,
        status=201,
    )

    rule = client.administratie(1).auto_booking_rules.create(
        naam="Bank costs",
        actie_type=AutoBookingActieType.ENKEL,
        tegenrekening_id=30,
        btw_code_id=50,
        iban_tegenpartij="DE75512308000000060004",
    )

    assert rule.id == 70
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["tegenrekening_id"] == 30
    assert body["btw_code_id"] == 50
    assert body["iban_tegenpartij"] == "DE75512308000000060004"
    assert "lines" not in body


def test_update(mocked_responses, client):
    updated = {
        **AUTO_BOOKING_RULE,
        "naam": "Updated name",
        "prioriteit": 5,
        "omschrijving_regex": "UPDATED",
    }
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/regels/70",
        json=updated,
    )
    rule = client.administratie(1).auto_booking_rules.update(
        70, naam="Updated name", prioriteit=5, omschrijving_regex="UPDATED"
    )
    assert rule.naam == "Updated name"
    assert rule.prioriteit == 5
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["naam"] == "Updated name"
    assert body["prioriteit"] == 5
    assert body["omschrijving_regex"] == "UPDATED"


def test_update_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/regels/999",
        json={"error": "Not found"},
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.administratie(1).auto_booking_rules.update(999, naam="x")


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE,
        f"{BASE_URL}/api/administraties/1/regels/70",
        status=204,
    )
    client.administratie(1).auto_booking_rules.delete(70)  # should not raise


def test_delete_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE,
        f"{BASE_URL}/api/administraties/1/regels/999",
        json={"error": "Not found"},
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.administratie(1).auto_booking_rules.delete(999)


def test_apply_to_boeking_matched(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekingen/100/apply-rules",
        json={"matched": True},
    )
    matched = client.administratie(1).auto_booking_rules.apply_to_boeking(100)
    assert matched is True


def test_apply_to_boeking_not_matched(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekingen/100/apply-rules",
        json={"matched": False},
    )
    matched = client.administratie(1).auto_booking_rules.apply_to_boeking(100)
    assert matched is False


def test_list_server_error(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels",
        json={"error": "Internal server error"},
        status=500,
    )
    with pytest.raises(MboekError) as exc_info:
        client.administratie(1).auto_booking_rules.list()
    assert exc_info.value.status_code == 500
