"""Tests for the boekingen resource."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
import responses

from mboek import (
    CreateBoekingInput,
    CreateBoekingsregelInput,
    NewBoeking,
    NewBoekingsregel,
)
from mboek.models._enums import Regeltype
from tests.conftest import BASE_URL, BOEKING_MET_REGELS, GROOTBOEKREKENING


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=[BOEKING_MET_REGELS],
    )
    items = client.administratie(1).boekjaar(10).dagboek(20).boekingen.list()
    assert len(items) == 1
    assert items[0].boeking.datum == date(2024, 1, 15)
    assert len(items[0].regels) == 2


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING_MET_REGELS
    )
    item = client.boekingen.get(100)
    assert item.boeking.id == 100


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=BOEKING_MET_REGELS,
        status=201,
    )
    regels = [
        CreateBoekingsregelInput(
            grootboekrekening_id=30,
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        CreateBoekingsregelInput(
            grootboekrekening_id=31,
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]
    inp = CreateBoekingInput(
        datum=date(2024, 1, 15),
        omschrijving="Test",
        regels=regels,
    )
    item = client.administratie(1).boekjaar(10).dagboek(20).boekingen.create(inp)
    assert item.boeking.id == 100


def test_create_serialises_cents():
    """Verify bedrag is converted from euros to cents in to_dict()."""
    regel = CreateBoekingsregelInput(
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
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/boekingen/100", json=BOEKING_MET_REGELS
    )
    item = client.boekingen.get(100)
    # BOEKING_REGEL has bedrag = -10000 cents → -€100.00
    assert item.regels[0].bedrag == Decimal("-100.00")
    # BOEKING_REGEL2 has bedrag = 10000 cents → €100.00
    assert item.regels[1].bedrag == Decimal("100.00")


# ── New name tests ────────────────────────────────────────────────────────────


def test_new_names_are_canonical():
    """New class names are importable from mboek directly."""
    assert NewBoeking is not None
    assert NewBoekingsregel is not None


def test_old_names_are_aliases():
    """Old Create...Input names still work as aliases for backward compat."""
    assert CreateBoekingInput is NewBoeking
    assert CreateBoekingsregelInput is NewBoekingsregel


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
    """NewBoekingsregel created with naam/code resolves to the correct IDs."""
    gbr2 = {**GROOTBOEKREKENING, "id": 31, "naam": "Kosten", "code": "4000"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING, gbr2],
    )
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/dagboeken/20/boekingen",
        json=BOEKING_MET_REGELS,
        status=201,
    )

    regels = [
        NewBoekingsregel(
            grootboekrekening_naam="Bank",
            omschrijving="Bank",
            bedrag=Decimal("-100.00"),
        ),
        NewBoekingsregel(
            grootboekrekening_code="4000",
            omschrijving="Kosten",
            bedrag=Decimal("100.00"),
        ),
    ]
    inp = NewBoeking(datum=date(2024, 1, 15), omschrijving="Test", regels=regels)
    item = client.administratie(1).boekjaar(10).dagboek(20).boekingen.create(inp)
    assert item.boeking.id == 100
    # Both regels should have been resolved
    assert regels[0].grootboekrekening_id == 30
    assert regels[1].grootboekrekening_id == 31


def test_regel_to_dict_unresolved_raises():
    """to_dict() raises if grootboekrekening_id was not resolved yet."""
    regel = NewBoekingsregel(
        grootboekrekening_naam="Bank",
        omschrijving="x",
        bedrag=Decimal("1.00"),
    )
    with pytest.raises(ValueError, match="not yet resolved"):
        regel.to_dict()
