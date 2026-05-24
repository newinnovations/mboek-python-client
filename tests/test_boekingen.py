"""Tests for the boekingen resource."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
import responses

from mboek import NewBoekingsregel, Regeltype
from tests.conftest import (
    ADMINISTRATIE,
    BASE_URL,
    BOEKING,
    BOEKING_REGEL,
    BOEKING_REGEL2,
    BOEKJAAR,
    DAGBOEK,
    GROOTBOEKREKENING,
)


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=[BOEKING],
    )
    items = client.administratie(1).boekjaar(10).dagboek(20).boekingen.list()
    assert len(items) == 1
    assert items[0].datum == date(2024, 1, 15)
    assert len(items[0].regels) == 2
    boeking_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/dagboeken/20/boekingen")
    ]
    assert "boekjaar_id=10" in boeking_calls[-1].request.url
    assert "limit=1000" in boeking_calls[-1].request.url
    assert "offset=0" in boeking_calls[-1].request.url


def test_list_filters(mocked_responses, client):
    other = {
        **BOEKING,
        "id": 101,
        "stuknummer": "INV-2",
        "omschrijving": "Other boeking",
    }
    filtered = {**BOEKING, "stuknummer": "INV-1"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=[filtered, other],
    )
    items = (
        client.administratie(1)
        .boekjaar(10)
        .dagboek(20)
        .boekingen.list(id=101, item="INV-2", description="Other boeking")
    )
    assert len(items) == 1
    assert items[0].id == 101


def test_get(mocked_responses, client):
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    item = client.boekingen.get(100)
    assert item.id == 100


def test_get_requires_booking_status(mocked_responses, client):
    invalid = {k: v for k, v in BOEKING.items() if k != "status"}
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=invalid)

    with pytest.raises(ValueError, match="status"):
        client.boekingen.get(100)


def test_get_requires_regel_omschrijving(mocked_responses, client):
    invalid = {
        **BOEKING,
        "regels": [
            {k: v for k, v in BOEKING_REGEL.items() if k != "omschrijving"},
            BOEKING_REGEL2,
        ],
    }
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=invalid)

    with pytest.raises(ValueError, match="omschrijving"):
        client.boekingen.get(100)


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=BOEKING,
        status=201,
    )
    regels = [
        NewBoekingsregel(
            grootboekrekening_id=30,
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_id=31,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]
    item = (
        client.administratie(1)
        .boekjaar(10)
        .dagboek(20)
        .boekingen.create(
            regels=regels,
            datum=date(2024, 1, 15),
            omschrijving="Test",
        )
    )
    assert item.id == 100
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["boekjaar_id"] == 10


def test_create_serialises_cents():
    """Verify bedrag is converted from euros to cents in to_dict()."""
    regel = NewBoekingsregel(
        grootboekrekening_id=1,
        omschrijving="x",
        bedrag=Decimal("12.34"),
    )
    d = regel.to_dict()
    assert d["bedrag"] == 1234  # 12.34 * 100


def test_delete(mocked_responses, client):
    mocked_responses.add(responses.DELETE, f"{BASE_URL}/api/boekingen/100", status=204)
    client.boekingen.delete(100)


def test_boeking_bedrag_parsed_from_cents(mocked_responses, client):
    """Verify bedrag is converted from cents to euros when parsing."""
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    item = client.boekingen.get(100)
    # BOEKING_REGEL has bedrag = -10000 cents → -€100.00
    assert item.regels[0].bedrag == Decimal("-100.00")
    # BOEKING_REGEL2 has bedrag = 10000 cents → €100.00
    assert item.regels[1].bedrag == Decimal("100.00")


def test_boeking_supports_new_regeltypes(mocked_responses, client):
    boeking = {
        **BOEKING,
        "regels": [
            {
                **BOEKING_REGEL,
                "id": 201,
                "regeltype": "btw_input",
                "netto_id": 102,
            },
            {
                **BOEKING_REGEL2,
                "id": 202,
                "regeltype": "btw_output",
                "netto_id": 101,
            },
        ],
    }
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=boeking)

    item = client.boekingen.get(100)

    assert item.regels[0].regeltype == Regeltype.BTW_INPUT
    assert item.regels[1].regeltype == Regeltype.BTW_OUTPUT


def test_create_serialises_new_regeltype_values():
    regel = NewBoekingsregel(
        grootboekrekening_id=1,
        omschrijving="BTW",
        bedrag=Decimal("2.10"),
        regeltype=Regeltype.BTW_INPUT,
        netto_ref=0,
    )

    d = regel.to_dict()

    assert d["regeltype"] == "btw_input"
    assert d["netto_ref"] == 0


# ── NewBoekingsregel validation ───────────────────────────────────────────────


def test_regel_validation_no_rekening():
    """NewBoekingsregel raises if no rekening identifier is provided."""
    with pytest.raises(ValueError, match="Provide exactly one"):
        NewBoekingsregel(omschrijving="x", bedrag=Decimal("1.00"))


def test_regel_validation_multiple_rekening():
    """NewBoekingsregel raises if more than one rekening identifier is provided."""
    with pytest.raises(ValueError, match="Provide only one"):
        NewBoekingsregel(
            omschrijving="x",
            bedrag=Decimal("1.00"),
            grootboekrekening_id=1,
            grootboekrekening_naam="Bank",
        )


def test_regel_with_naam(mocked_responses, client):
    """Name/code resolution happens in the payload without mutating the input DTOs."""
    gbr2 = {**GROOTBOEKREKENING, "id": 31, "naam": "Kosten", "code": 4000}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING, gbr2],
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=BOEKING,
        status=201,
    )

    regels = [
        NewBoekingsregel(
            grootboekrekening_naam="Bank",
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_code=4000,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]
    item = (
        client.administratie(1)
        .boekjaar(10)
        .dagboek(20)
        .boekingen.create(
            regels=regels,
            datum=date(2024, 1, 15),
            omschrijving="Test",
        )
    )
    assert item.id == 100
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["regels"][0]["grootboekrekening_id"] == 30
    assert body["regels"][1]["grootboekrekening_id"] == 31
    assert regels[0].grootboekrekening_id is None
    assert regels[0].grootboekrekening_naam == "Bank"
    assert regels[1].grootboekrekening_id is None
    assert regels[1].grootboekrekening_code == 4000


def test_regel_to_dict_unresolved_raises():
    """to_dict() raises if grootboekrekening_id was not resolved yet."""
    regel = NewBoekingsregel(
        grootboekrekening_naam="Bank",
        omschrijving="x",
        bedrag=Decimal("1.00"),
    )
    with pytest.raises(ValueError, match="not yet resolved"):
        regel.to_dict()


def test_update_regels_with_naam_resolves_without_mutating(mocked_responses, client):
    gbr2 = {**GROOTBOEKREKENING, "id": 31, "naam": "Kosten", "code": 4000}
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties",
        json=[ADMINISTRATIE],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING, gbr2],
    )
    mocked_responses.add(responses.PATCH, f"{BASE_URL}/api/boekingen/100", json=BOEKING)

    regels = [
        NewBoekingsregel(
            grootboekrekening_naam="Bank",
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_code=4000,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]
    item = client.boekingen.update(100, regels=regels)

    assert item.id == 100
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["regels"][0]["grootboekrekening_id"] == 30
    assert body["regels"][1]["grootboekrekening_id"] == 31
    assert regels[0].grootboekrekening_id is None
    assert regels[0].grootboekrekening_naam == "Bank"
    assert regels[1].grootboekrekening_id is None
    assert regels[1].grootboekrekening_code == 4000


def test_update_regels_with_admin_id_skips_owner_lookup(mocked_responses, client):
    gbr2 = {**GROOTBOEKREKENING, "id": 31, "naam": "Kosten", "code": 4000}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING, gbr2],
    )
    mocked_responses.add(responses.PATCH, f"{BASE_URL}/api/boekingen/100", json=BOEKING)

    regels = [
        NewBoekingsregel(
            grootboekrekening_naam="Bank",
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_code=4000,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]

    start = len(mocked_responses.calls)
    item = client.boekingen.update(100, admin_id=1, regels=regels)

    assert item.id == 100
    new_calls = mocked_responses.calls[start:]
    assert len(new_calls) == 2
    assert new_calls[0].request.url.startswith(
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen"
    )
    assert new_calls[1].request.url == f"{BASE_URL}/api/boekingen/100"


def test_update_regels_with_ids_preserves_admin_scope(mocked_responses, client):
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties",
        json=[ADMINISTRATIE],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(responses.PATCH, f"{BASE_URL}/api/boekingen/100", json=BOEKING)

    regels = [
        NewBoekingsregel(
            grootboekrekening_id=30,
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_id=31,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]

    item = client.boekingen.update(100, regels=regels)

    assert item._administratie_id == 1
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["regels"][0]["grootboekrekening_id"] == 30
    assert body["regels"][1]["grootboekrekening_id"] == 31


# ── Unified boekingen via with_boekjaar ───────────────────────────────────────


def test_boekingen_via_with_boekjaar(mocked_responses, client):
    """Dagboek obtained from dagboeken.list(code=...) gets boekingen via with_boekjaar."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=[BOEKING],
    )
    dagboek = client.administratie(1).dagboeken.list(code="BANK")[0]
    scoped = dagboek.with_boekjaar(id=10)
    items = scoped.boekingen.list()
    assert len(items) == 1


# ── Scoped Boeking instance methods ──────────────────────────────────────────


def test_list_items_are_scoped(mocked_responses, client):
    """Boekingen returned from list() carry a client reference."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren/10",
        json=BOEKJAAR,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken/20",
        json=DAGBOEK,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=[BOEKING],
    )
    items = client.administratie(1).boekjaar(10).dagboek(20).boekingen.list()
    assert items[0]._client is client


def test_get_is_scoped(mocked_responses, client):
    """Boeking returned from get() carries a client reference."""
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    boeking = client.boekingen.get(100)
    assert boeking._client is client


def test_boeking_delete_via_instance(mocked_responses, client):
    """boeking.delete() calls DELETE /api/boekingen/{id}."""
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    mocked_responses.add(responses.DELETE, f"{BASE_URL}/api/boekingen/100", status=204)
    boeking = client.boekingen.get(100)
    boeking.delete()


def test_boeking_update_via_instance(mocked_responses, client):
    """boeking.update() refreshes the current instance after PATCH."""
    updated = {**BOEKING, "omschrijving": "Updated"}
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING)
    mocked_responses.add(responses.PATCH, f"{BASE_URL}/api/boekingen/100", json=updated)
    boeking = client.boekingen.get(100)
    result = boeking.update(omschrijving="Updated")
    assert result is boeking
    assert result.omschrijving == "Updated"
    assert boeking.omschrijving == "Updated"
    assert result._client is client


def test_boeking_delete_without_client_raises(client):
    """Boeking.delete() raises ScopeError when no client reference is set."""
    from mboek import ScopeError
    from mboek._parsers import parse_boeking_met_regels

    boeking = parse_boeking_met_regels(BOEKING)  # no client
    with pytest.raises(ScopeError):
        boeking.delete()


def test_boeking_update_without_client_raises(client):
    """Boeking.update() raises ScopeError when no client reference is set."""
    from mboek import ScopeError
    from mboek._parsers import parse_boeking_met_regels

    boeking = parse_boeking_met_regels(BOEKING)  # no client
    with pytest.raises(ScopeError):
        boeking.update(omschrijving="x")
