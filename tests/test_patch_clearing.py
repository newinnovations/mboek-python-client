"""Regression tests for explicit null-clearing in PATCH wrappers."""

from __future__ import annotations

import json

import responses

from tests.conftest import (
    ADMINISTRATIE,
    BASE_URL,
    BOEKING,
    BOEKJAAR,
    BTW_CODE,
    DAGBOEK,
    GROOTBOEKREKENING,
)

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
    "lines": [],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


def _request_body(mocked_responses):
    return json.loads(mocked_responses.calls[-1].request.body)


def test_administraties_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH, f"{BASE_URL}/api/administraties/1", json=ADMINISTRATIE
    )

    client.administraties.update(1, adres=None, huidig_boekjaar_id=None)

    body = _request_body(mocked_responses)
    assert body["adres"] is None
    assert body["huidig_boekjaar_id"] is None


def test_boekjaren_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )

    client.administratie(1).boekjaren.update(
        10, naam=None, start_datum=None, eind_datum=None
    )

    body = _request_body(mocked_responses)
    assert body["naam"] is None
    assert body["start_datum"] is None
    assert body["eind_datum"] is None


def test_dagboeken_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )

    client.administratie(1).dagboeken.update(20, grootboekrekening_id=None, iban=None)

    body = _request_body(mocked_responses)
    assert body["grootboekrekening_id"] is None
    assert body["iban"] is None


def test_btw_codes_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/btw-codes/50",
        json=BTW_CODE,
    )

    client.administratie(1).btw_codes.update(
        50,
        output_rekening_id=None,
        input_rekening_id=None,
        pct_aftrek=None,
    )

    body = _request_body(mocked_responses)
    assert body["output_rekening_id"] is None
    assert body["input_rekening_id"] is None
    assert body["pct_aftrek"] is None


def test_grootboekrekeningen_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/30",
        json=GROOTBOEKREKENING,
    )

    client.administratie(1).grootboekrekeningen.update(
        30,
        parent_id=None,
        default_btw_id=None,
        rgs_code=None,
    )

    body = _request_body(mocked_responses)
    assert body["parent_id"] is None
    assert body["default_btw_id"] is None
    assert body["rgs_code"] is None


def test_boekingen_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(responses.PATCH, f"{BASE_URL}/api/boekingen/100", json=BOEKING)

    client.boekingen.update(
        100,
        stuknummer=None,
        tegenpartij_naam=None,
        tegenpartij_iban=None,
    )

    body = _request_body(mocked_responses)
    assert body["stuknummer"] is None
    assert body["tegenpartij_naam"] is None
    assert body["tegenpartij_iban"] is None


def test_auto_booking_rules_update_can_clear_nullable_fields(mocked_responses, client):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE_URL}/api/administraties/1/regels/70",
        json=AUTO_BOOKING_RULE,
    )

    client.administratie(1).auto_booking_rules.update(
        70,
        iban_eigen=None,
        iban_tegenpartij=None,
        omschrijving_regex=None,
        tegenrekening_id=None,
        btw_code_id=None,
        lines=None,
    )

    body = _request_body(mocked_responses)
    assert body["iban_eigen"] is None
    assert body["iban_tegenpartij"] is None
    assert body["omschrijving_regex"] is None
    assert body["tegenrekening_id"] is None
    assert body["btw_code_id"] is None
    assert body["lines"] is None
