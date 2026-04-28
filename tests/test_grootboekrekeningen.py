"""Tests for the grootboekrekeningen resource."""

from __future__ import annotations

import responses

from mboek.models._enums import RekeningCategorie, RekeningType
from tests.conftest import BASE_URL, GROOTBOEKREKENING


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    items = client.administratie(1).grootboekrekeningen.list()
    assert len(items) == 1
    assert items[0].code == "1220"
    assert items[0].rekening_type == RekeningType.ACTIVA


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/30",
        json=GROOTBOEKREKENING,
    )
    item = client.administratie(1).grootboekrekeningen.get(30)
    assert item.naam == "Bank"


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=GROOTBOEKREKENING,
        status=201,
    )
    item = client.administratie(1).grootboekrekeningen.create(
        code="1220",
        naam="Bank",
        rekening_type=RekeningType.ACTIVA,
        categorie=RekeningCategorie.BALANS,
    )
    assert item.id == 30


def test_seed_rgs(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/seed-rgs",
        status=204,
    )
    client.administratie(1).grootboekrekeningen.seed_rgs()  # should not raise


def test_met_saldo(mocked_responses, client):
    data = [{"rekening": GROOTBOEKREKENING, "aantal_transacties": 5, "saldo": 100000}]
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=data,
    )
    items = client.administratie(1).grootboekrekeningen.met_saldo(10)
    assert items[0].saldo == 1000  # 100000 cents → €1000.00


def test_mutaties(mocked_responses, client):
    mutatie = {
        "regel_id": 1,
        "boeking_id": 100,
        "dagboek_id": 20,
        "datum": "2024-01-15",
        "dagboek_code": "BANK",
        "dagboek_naam": "Bankboek",
        "boeking_omschrijving": "Test",
        "regel_omschrijving": "Regel",
        "bedrag": -10000,
    }
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/rekening/30/mutaties",
        json=[mutatie],
    )
    items = client.administratie(1).grootboekrekeningen.mutaties(30, 10)
    from decimal import Decimal

    assert items[0].bedrag == Decimal("-100.00")


def test_find_by_naam_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    result = client.administratie(1).grootboekrekeningen.find_by_naam("Bank")
    assert result is not None
    assert result.id == 30


def test_find_by_naam_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    result = client.administratie(1).grootboekrekeningen.find_by_naam("Kas")
    assert result is None


def test_find_by_code_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    result = client.administratie(1).grootboekrekeningen.find_by_code("1220")
    assert result is not None
    assert result.naam == "Bank"


def test_find_by_code_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    result = client.administratie(1).grootboekrekeningen.find_by_code("9999")
    assert result is None


# ── Cache tests ───────────────────────────────────────────────────────────────


def test_list_cached(mocked_responses, client):
    """list() is served from cache on the second call; only one HTTP request is made."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    gbr = client.administratie(1).grootboekrekeningen
    first = gbr.list()
    second = gbr.list()
    assert first == second
    # Only one HTTP call despite two list() calls
    gbr_calls = [
        c
        for c in mocked_responses.calls
        if "grootboekrekeningen" in c.request.url and "met-saldo" not in c.request.url
    ]
    assert len(gbr_calls) == 1


def test_list_refresh_bypasses_cache(mocked_responses, client):
    """list(refresh=True) bypasses the cache and fetches fresh data."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    gbr = client.administratie(1).grootboekrekeningen
    gbr.list()
    gbr.list(refresh=True)
    gbr_calls = [
        c
        for c in mocked_responses.calls
        if "grootboekrekeningen" in c.request.url and "met-saldo" not in c.request.url
    ]
    assert len(gbr_calls) == 2


def test_clear_cache(mocked_responses, client):
    """clear_cache() causes the next list() to fetch fresh data."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    gbr = client.administratie(1).grootboekrekeningen
    gbr.list()
    gbr.clear_cache()
    gbr.list()
    gbr_calls = [
        c
        for c in mocked_responses.calls
        if "grootboekrekeningen" in c.request.url and "met-saldo" not in c.request.url
    ]
    assert len(gbr_calls) == 2


def test_find_by_naam_uses_cache(mocked_responses, client):
    """find_by_naam and find_by_code share the same cached list."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen",
        json=[GROOTBOEKREKENING],
    )
    gbr = client.administratie(1).grootboekrekeningen
    r1 = gbr.find_by_naam("Bank")
    r2 = gbr.find_by_code("1220")
    assert r1 is not None
    assert r2 is not None
    # Only one HTTP request for two lookups
    gbr_calls = [
        c
        for c in mocked_responses.calls
        if "grootboekrekeningen" in c.request.url and "met-saldo" not in c.request.url
    ]
    assert len(gbr_calls) == 1


# ── Unified domain object tests ───────────────────────────────────────────────


def test_grootboekrekening_saldo_scope_error(mocked_responses, client):
    """Accessing saldo without boekjaar scope raises ScopeError."""
    from mboek._exceptions import ScopeError

    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/30",
        json=GROOTBOEKREKENING,
    )
    gbr = client.administratie(1).grootboekrekeningen.get(30)
    try:
        _ = gbr.saldo
        assert False
    except ScopeError:
        pass


def test_grootboekrekening_with_boekjaar(mocked_responses, client):
    """with_boekjaar() sets scope; without_boekjaar() removes it."""
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/30",
        json=GROOTBOEKREKENING,
    )
    gbr = client.administratie(1).grootboekrekeningen.get(30)
    scoped = gbr.with_boekjaar(boekjaar_id=10)
    assert scoped is not gbr
    assert scoped._boekjaar_id == 10
    assert gbr._boekjaar_id is None

    unscoped = scoped.without_boekjaar()
    assert unscoped._boekjaar_id is None


def test_grootboekrekening_lazy_saldo(mocked_responses, client):
    """saldo is lazily fetched via met-saldo when boekjaar scope is set."""
    from decimal import Decimal

    data = [{"rekening": GROOTBOEKREKENING, "aantal_transacties": 2, "saldo": 50000}]
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/30",
        json=GROOTBOEKREKENING,
    )
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/grootboekrekeningen/met-saldo/10",
        json=data,
    )
    gbr = client.administratie(1).grootboekrekeningen.get(30)
    scoped = gbr.with_boekjaar(boekjaar_id=10)
    assert scoped.saldo == Decimal("500.00")
    # Second access is cached — no additional HTTP call
    assert scoped.saldo == Decimal("500.00")
    saldo_calls = [c for c in mocked_responses.calls if "met-saldo" in c.request.url]
    assert len(saldo_calls) == 1
