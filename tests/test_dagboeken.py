"""Tests for the dagboeken resource."""

from __future__ import annotations

import pytest
import responses

from mboek import CreateDagboekInput, NewDagboek
from mboek.models._enums import DagboekType
from tests.conftest import BASE_URL, DAGBOEK, GROOTBOEKREKENING


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    items = client.administratie(1).dagboeken.list()
    assert len(items) == 1
    assert items[0].code == "BANK"
    assert items[0].dagboek_type == DagboekType.BANK


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    item = client.administratie(1).dagboeken.get(20)
    assert item.naam == "Bankboek"


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=DAGBOEK,
        status=201,
    )
    inp = CreateDagboekInput(
        code="BANK", naam="Bankboek", dagboek_type=DagboekType.BANK
    )
    item = client.administratie(1).dagboeken.create(inp)
    assert item.id == 20


def test_werkstatus(mocked_responses, client):
    ws = [{"dagboek_id": 20, "onverwerkt": 3, "te_bevestigen": 1}]
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/werkstatus", json=ws
    )
    items = client.administratie(1).dagboeken.werkstatus(boekjaar_id=10)
    assert items[0].dagboek_id == 20
    assert items[0].onverwerkt == 3


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1/dagboeken/20", status=204
    )
    client.administratie(1).dagboeken.delete(20)


def test_find_by_naam_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_naam("Bankboek")
    assert result is not None
    assert result.id == 20


def test_find_by_naam_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_naam("Onbekend")
    assert result is None


def test_find_by_code_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_code("bank")  # case-insensitive
    assert result is not None
    assert result.code == "BANK"


def test_find_by_code_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    result = client.administratie(1).dagboeken.find_by_code("KAS")
    assert result is None


def test_dagboek_scope_by_id(client):
    """Positional and keyword ID still work without an HTTP call (AdministratieScope)."""
    scope = client.administratie(1).dagboek(20)
    assert scope._dagboek_id == 20

    scope = client.administratie(1).dagboek(dagboek_id=20)
    assert scope._dagboek_id == 20


def test_dagboek_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).dagboek(name="Bankboek")
    assert scope._dagboek_id == 20


def test_dagboek_scope_by_code(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).dagboek(code="bank")  # case-insensitive
    assert scope._dagboek_id == 20


def test_dagboek_scope_by_name_not_found(mocked_responses, client):
    from mboek._exceptions import NotFoundError

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    try:
        client.administratie(1).dagboek(name="Onbekend")
        assert False
    except NotFoundError as e:
        assert "Onbekend" in str(e)


def test_dagboek_scope_by_code_not_found(mocked_responses, client):
    from mboek._exceptions import NotFoundError

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    try:
        client.administratie(1).dagboek(code="KAS")
        assert False
    except NotFoundError as e:
        assert "KAS" in str(e)


def test_dagboek_scope_missing_args(client):
    try:
        client.administratie(1).dagboek()
        assert False
    except ValueError:
        pass


def test_boekjaar_dagboek_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).boekjaar(10).dagboek(name="Bankboek")
    assert scope._dagboek_id == 20


def test_boekjaar_dagboek_scope_by_code(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).boekjaar(10).dagboek(code="BANK")
    assert scope._dagboek_id == 20


def test_boekjaar_dagboek_scope_by_name_not_found(mocked_responses, client):
    from mboek._exceptions import NotFoundError

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    try:
        client.administratie(1).boekjaar(10).dagboek(name="Onbekend")
        assert False
    except NotFoundError:
        pass


# ── New names & naam/code resolution ─────────────────────────────────────────


def test_new_dagboek_name_is_canonical():
    """NewDagboek is importable and is the canonical class."""
    assert NewDagboek is not None
    assert CreateDagboekInput is NewDagboek


def test_create_dagboek_with_rekening_naam(mocked_responses, client):
    """Creating a dagboek using grootboekrekening_naam resolves the ID automatically."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    dagboek_with_rekening = {**DAGBOEK, "grootboekrekening_id": 30}
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=dagboek_with_rekening,
        status=201,
    )
    inp = NewDagboek(
        code="BANK",
        naam="Bankboek",
        dagboek_type=DagboekType.BANK,
        grootboekrekening_naam="Bank",
    )
    item = client.administratie(1).dagboeken.create(inp)
    assert item.id == 20
    assert inp.grootboekrekening_id == 30


def test_create_dagboek_with_rekening_code(mocked_responses, client):
    """Creating a dagboek using grootboekrekening_code resolves the ID automatically."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    dagboek_with_rekening = {**DAGBOEK, "grootboekrekening_id": 30}
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=dagboek_with_rekening,
        status=201,
    )
    inp = NewDagboek(
        code="BANK",
        naam="Bankboek",
        dagboek_type=DagboekType.BANK,
        grootboekrekening_code="1220",
    )
    item = client.administratie(1).dagboeken.create(inp)
    assert item.id == 20
    assert inp.grootboekrekening_id == 30


def test_new_dagboek_validation_multiple_rekening():
    """NewDagboek raises if more than one rekening identifier is provided."""
    with pytest.raises(ValueError, match="Provide only one"):
        NewDagboek(
            code="BANK",
            naam="Bankboek",
            dagboek_type=DagboekType.BANK,
            grootboekrekening_id=30,
            grootboekrekening_naam="Bank",
        )
