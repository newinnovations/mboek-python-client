"""Tests for the automatic booking rules resource."""

from __future__ import annotations

import responses

from mboek.models._enums import AutoBookingActieType
from tests.conftest import BASE_URL

AUTO_BOOKING_RULE = {
    "id": 70,
    "administratie_id": 1,
    "naam": "Bank costs",
    "prioriteit": 10,
    "actief": True,
    "actie_type": "enkel",
    "eigen_iban_patroon": None,
    "tegenpartij_iban_patroon": None,
    "omschrijving_patroon": "KOSTEN",
    "lines": [
        {
            "id": 1,
            "rule_id": 70,
            "volgorde": 1,
            "grootboekrekening_id": 30,
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
