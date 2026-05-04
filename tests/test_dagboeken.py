"""Tests for the dagboeken resource."""

from __future__ import annotations

import pytest
import responses

from mboek._exceptions import NotFoundError, ScopeError
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
    dagboek_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/administraties/1/dagboeken")
    ]
    assert "limit=1000" in dagboek_calls[-1].request.url
    assert "offset=0" in dagboek_calls[-1].request.url


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    item = client.administratie(1).dagboeken.get(20)
    assert item.naam == "Bankboek"


def test_get_supports_beginbalans_type(mocked_responses, client):
    dagboek = {
        **DAGBOEK,
        "id": 21,
        "code": "BB",
        "naam": "Beginbalans",
        "dagboek_type": "beginbalans",
    }
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/21", json=dagboek
    )

    item = client.administratie(1).dagboeken.get(21)

    assert item.dagboek_type == DagboekType.BEGINBALANS


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=DAGBOEK,
        status=201,
    )
    item = client.administratie(1).dagboeken.create(
        code="BANK", naam="Bankboek", dagboek_type=DagboekType.BANK
    )
    assert item.id == 20


def test_werkstatus(mocked_responses, client):
    ws = [{"dagboek_id": 20, "onverwerkt": 3, "te_bevestigen": 1}]
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/werkstatus", json=ws
    )
    items = client.administratie(1).dagboeken.werkstatus(boekjaar_id=10)
    assert items[0].dagboek_id == 20
    assert items[0].onverwerkt == 3
    werkstatus_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(
            f"{BASE_URL}/api/administraties/1/dagboeken/werkstatus"
        )
    ]
    assert "boekjaar_id=10" in werkstatus_calls[-1].request.url
    assert "limit=1000" in werkstatus_calls[-1].request.url
    assert "offset=0" in werkstatus_calls[-1].request.url


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1/dagboeken/20", status=204
    )
    client.administratie(1).dagboeken.delete(20)


def test_list_filters(mocked_responses, client):
    other = {**DAGBOEK, "id": 21, "code": "KAS", "naam": "Kasboek"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, other],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, other],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, other],
    )
    by_name = client.administratie(1).dagboeken.list(name="Bankboek")
    assert len(by_name) == 1
    assert by_name[0].id == 20

    by_code = client.administratie(1).dagboeken.list(code="kas")
    assert len(by_code) == 1
    assert by_code[0].id == 21

    by_id = client.administratie(1).dagboeken.list(id=20)
    assert len(by_id) == 1
    assert by_id[0].code == "BANK"


def test_list_filters_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    assert client.administratie(1).dagboeken.list(name="Onbekend") == []
    assert client.administratie(1).dagboeken.list(code="KAS") == []


def test_dagboek_scope_by_id(mocked_responses, client):
    """Positional and keyword ID make one GET call and return a full Dagboek."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    scope = client.administratie(1).dagboek(20)
    assert scope.id == 20
    assert scope.naam == "Bankboek"

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    scope = client.administratie(1).dagboek(id=20)
    assert scope.id == 20


def test_dagboek_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).dagboek(name="Bankboek")
    assert scope.id == 20


def test_dagboek_scope_by_code(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).dagboek(code="bank")  # case-insensitive
    assert scope.id == 20

def test_dagboek_scope_by_name_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administratie(1).dagboek(name="Onbekend")
    assert "Onbekend" in str(exc_info.value)


def test_dagboek_scope_by_name_requires_single_match(mocked_responses, client):
    duplicate = {**DAGBOEK, "id": 21, "code": "BNK2"}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, duplicate],
    )
    with pytest.raises(ValueError, match="Bankboek"):
        client.administratie(1).dagboek(name="Bankboek")


def test_dagboek_scope_by_code_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administratie(1).dagboek(code="KAS")
    assert "KAS" in str(exc_info.value)


def test_dagboek_scope_missing_args(client):
    with pytest.raises(ValueError):
        client.administratie(1).dagboek()


def test_boekjaar_dagboek_scope_by_name(mocked_responses, client):
    from tests.conftest import BOEKJAAR

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).boekjaar(10).dagboek(name="Bankboek")
    assert scope.id == 20
    assert scope._boekjaar_id == 10


def test_boekjaar_dagboek_scope_by_code(mocked_responses, client):
    from tests.conftest import BOEKJAAR

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    scope = client.administratie(1).boekjaar(10).dagboek(code="BANK")
    assert scope.id == 20
    assert scope._boekjaar_id == 10


def test_boekjaar_dagboek_scope_by_name_not_found(mocked_responses, client):
    from tests.conftest import BOEKJAAR

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    with pytest.raises(NotFoundError):
        client.administratie(1).boekjaar(10).dagboek(name="Onbekend")


def test_boekjaar_dagboek_scope_by_name_requires_single_match(mocked_responses, client):
    from tests.conftest import BOEKJAAR

    duplicate = {**DAGBOEK, "id": 21, "code": "BNK2"}
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/boekjaren/10", json=BOEKJAAR
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/dagboeken",
        json=[DAGBOEK, duplicate],
    )
    with pytest.raises(ValueError, match="Bankboek"):
        client.administratie(1).boekjaar(10).dagboek(name="Bankboek")


# ── New names & naam/code resolution ─────────────────────────────────────────


def test_create_dagboek_with_rekening_naam(mocked_responses, client):
    """Creating a dagboek using grootboekrekening_naam resolves the ID automatically."""
    import json as _json

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
    item = client.administratie(1).dagboeken.create(
        code="BANK",
        naam="Bankboek",
        dagboek_type=DagboekType.BANK,
        grootboekrekening_naam="Bank",
    )
    assert item.id == 20
    # Verify the resolved ID was sent in the request body
    body = _json.loads(mocked_responses.calls[-1].request.body)
    assert body["grootboekrekening_id"] == 30


def test_create_dagboek_with_rekening_code(mocked_responses, client):
    """Creating a dagboek using grootboekrekening_code resolves the ID automatically."""
    import json as _json

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
    item = client.administratie(1).dagboeken.create(
        code="BANK",
        naam="Bankboek",
        dagboek_type=DagboekType.BANK,
        grootboekrekening_code="1220",
    )
    assert item.id == 20
    body = _json.loads(mocked_responses.calls[-1].request.body)
    assert body["grootboekrekening_id"] == 30


def test_create_dagboek_validation_multiple_rekening(client):
    """create() raises if more than one rekening identifier is provided."""
    with pytest.raises(ValueError, match="Provide only one"):
        client.administratie(1).dagboeken.create(
            code="BANK",
            naam="Bankboek",
            dagboek_type=DagboekType.BANK,
            grootboekrekening_id=30,
            grootboekrekening_naam="Bank",
        )


# ── Unified domain object tests ───────────────────────────────────────────────


def test_dagboek_has_data_attrs(mocked_responses, client):
    """Dagboek returned by any path always has naam, code, etc."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    d = client.administratie(1).dagboeken.list(code="BANK")[0]
    assert d.naam == "Bankboek"
    assert d.code == "BANK"


def test_with_boekjaar_returns_new_object(mocked_responses, client):
    """with_boekjaar() returns a new Dagboek; original is not mutated."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken", json=[DAGBOEK]
    )
    d = client.administratie(1).dagboeken.list(code="BANK")[0]
    scoped = d.with_boekjaar(id=10)
    assert scoped is not d
    assert scoped._boekjaar_id == 10
    assert d._boekjaar_id is None  # original unchanged


def test_without_boekjaar_clears_scope(mocked_responses, client):
    """without_boekjaar() returns a new Dagboek with boekjaar scope removed."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    d = client.administratie(1).dagboek(20)
    scoped = d.with_boekjaar(id=10)
    unscoped = scoped.without_boekjaar()
    assert unscoped._boekjaar_id is None
    assert scoped._boekjaar_id == 10  # original scoped not mutated


def test_with_boekjaar_name_requires_single_match(mocked_responses, client):
    from tests.conftest import BOEKJAAR

    duplicate = {**BOEKJAAR, "id": 11}
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/boekjaren",
        json=[BOEKJAAR, duplicate],
    )
    dagboek = client.administratie(1).dagboek(20)
    with pytest.raises(ValueError, match="2024"):
        dagboek.with_boekjaar(name="2024")


def test_boekingen_scope_error(mocked_responses, client):
    """Accessing boekingen without a boekjaar scope raises ScopeError."""
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1/dagboeken/20", json=DAGBOEK
    )
    d = client.administratie(1).dagboek(20)
    with pytest.raises(ScopeError):
        _ = d.boekingen


# ── s11: Account name/code resolution error tests ────────────────────────────


def test_create_dagboek_unknown_rekening_naam_raises(mocked_responses, client):
    """create() with an unknown grootboekrekening_naam raises NotFoundError."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    with pytest.raises(NotFoundError, match="Onbekend"):
        client.administratie(1).dagboeken.create(
            code="BANK",
            naam="Bankboek",
            dagboek_type=DagboekType.BANK,
            grootboekrekening_naam="Onbekend",
        )


def test_create_dagboek_unknown_rekening_code_raises(mocked_responses, client):
    """create() with an unknown grootboekrekening_code raises NotFoundError."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    with pytest.raises(NotFoundError, match="9999"):
        client.administratie(1).dagboeken.create(
            code="BANK",
            naam="Bankboek",
            dagboek_type=DagboekType.BANK,
            grootboekrekening_code="9999",
        )


def test_create_dagboek_ambiguous_rekening_naam_raises(mocked_responses, client):
    """create() with an ambiguous grootboekrekening_naam raises ValueError."""
    duplicate = {**GROOTBOEKREKENING, "id": 31}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING, duplicate],
    )
    with pytest.raises(ValueError, match="Bank"):
        client.administratie(1).dagboeken.create(
            code="BANK",
            naam="Bankboek",
            dagboek_type=DagboekType.BANK,
            grootboekrekening_naam="Bank",
        )
