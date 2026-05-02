"""Tests for BTW-aangifte parsing."""

from __future__ import annotations

import responses

from mboek import BtwAangifteStatus
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
