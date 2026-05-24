"""Tests for the automatic booking rules resource."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
import responses

from mboek import (
    AutoBookingActieType,
    AutoBookingRuleApplicationResult,
    AutoBookingRulesExport,
    AutoBookingRulesImportResult,
    NewAutoBookingRuleLine,
)
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
AUTO_BOOKING_RULES_EXPORT = {
    "type": "auto_booking_rules",
    "rules": [
        {
            "naam": "Bank costs",
            "prioriteit": 10,
            "actie_type": "enkel",
            "tegenrekening_code": 1220,
        }
    ],
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


def test_export(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels/export",
        json=AUTO_BOOKING_RULES_EXPORT,
    )

    payload = client.administratie(1).auto_booking_rules.export()

    assert isinstance(payload, AutoBookingRulesExport)
    assert payload.type == "auto_booking_rules"
    assert payload.to_dict() == AUTO_BOOKING_RULES_EXPORT


def test_import(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/regels/import",
        json={"imported": 3, "replaced_existing": True},
    )

    result = client.administratie(1).auto_booking_rules.import_(
        AutoBookingRulesExport.from_dict(AUTO_BOOKING_RULES_EXPORT),
        replace=True,
    )

    assert isinstance(result, AutoBookingRulesImportResult)
    assert result.imported == 3
    assert result.replaced_existing is True
    assert mocked_responses.calls[-1].request.url.endswith(
        "/regels/import?replace=true"
    )
    assert (
        json.loads(mocked_responses.calls[-1].request.body) == AUTO_BOOKING_RULES_EXPORT
    )


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


def test_create_fixed_amount_line_serializes_bedrag_as_cents(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/regels",
        json=AUTO_BOOKING_RULE,
        status=201,
    )

    line = NewAutoBookingRuleLine(
        tegenrekening_id=30,
        bedrag_type=AutoBookingBedragType.VAST,
        bedrag=Decimal("12.34"),
    )
    client.administratie(1).auto_booking_rules.create(
        naam="Fixed split",
        actie_type=AutoBookingActieType.SPLITS,
        lines=[line],
    )

    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["lines"][0]["bedrag"] == 1234


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
    assert line.tegenrekening_id is None
    assert line.tegenrekening_naam == "Bank"


def test_update_lines_with_rekening_naam_resolves_without_mutating(
    mocked_responses, client
):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/regels/70",
        json=AUTO_BOOKING_RULE,
    )

    line = NewAutoBookingRuleLine(
        tegenrekening_naam="Bank", bedrag_type=AutoBookingBedragType.REST
    )
    rule = client.administratie(1).auto_booking_rules.update(70, lines=[line])

    assert rule.id == 70
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["lines"][0]["tegenrekening_id"] == 30
    assert line.tegenrekening_id is None
    assert line.tegenrekening_naam == "Bank"


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
    result = client.administratie(1).auto_booking_rules.apply_to_boeking(100)
    assert isinstance(result, AutoBookingRuleApplicationResult)
    assert result.matched is True
    assert result.reason is None
    assert bool(result) is True


def test_apply_to_boeking_not_matched(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekingen/100/apply-rules",
        json={"matched": False, "reason": "No matching rule"},
    )
    result = client.administratie(1).auto_booking_rules.apply_to_boeking(100)
    assert result.matched is False
    assert result.reason == "No matching rule"
    assert bool(result) is False


def test_apply_to_boeking_invalid_reason_type(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/boekingen/100/apply-rules",
        json={"matched": False, "reason": {"message": "invalid"}},
    )
    with pytest.raises(MboekError, match="reason"):
        client.administratie(1).auto_booking_rules.apply_to_boeking(100)


def test_list_requires_line_omschrijving(mocked_responses, client):
    lines = AUTO_BOOKING_RULE.get("lines")
    assert isinstance(lines, list)
    line = lines[0]
    assert isinstance(line, dict)
    invalid_rule = {
        **AUTO_BOOKING_RULE,
        "lines": [{k: v for k, v in line.items() if k != "omschrijving"}],
    }
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/regels",
        json=[invalid_rule],
    )

    with pytest.raises(ValueError, match="omschrijving"):
        client.administratie(1).auto_booking_rules.list()


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
