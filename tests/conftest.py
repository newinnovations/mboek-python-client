"""Shared pytest fixtures for mboek client tests."""

from __future__ import annotations

import pytest
import responses as resp_lib

from mboek import MboekClient

BASE_URL = "http://localhost:3000"

LOGIN_RESPONSE = {
    "token": "test-jwt-token",
    "gebruikersnaam": "admin",
    "expires_at": 9999999999,
}

ADMINISTRATIE = {
    "id": 1,
    "naam": "Test BV",
    "beschrijving": None,
    "kvk_nummer": None,
    "btw_nummer": None,
    "adres": None,
    "active": True,
    "huidig_boekjaar_id": None,
    "bankimport_rekening_id": None,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

BOEKJAAR = {
    "id": 10,
    "administratie_id": 1,
    "naam": "2024",
    "start_datum": "2024-01-01",
    "eind_datum": "2024-12-31",
    "status": "open",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

DAGBOEK = {
    "id": 20,
    "administratie_id": 1,
    "code": "BANK",
    "naam": "Bankboek",
    "dagboek_type": "bank",
    "grootboekrekening_id": None,
    "iban": None,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

GROOTBOEKREKENING = {
    "id": 30,
    "administratie_id": 1,
    "code": "1220",
    "naam": "Bank",
    "rekening_type": "activa",
    "categorie": "balans",
    "rgs_code": None,
    "parent_id": None,
    "default_btw_id": None,
    "actief": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

BOEKING_REGEL = {
    "id": 101,
    "boeking_id": 100,
    "grootboekrekening_id": 30,
    "omschrijving": "Test regel",
    "bedrag": -10000,  # -€100.00 in cents
    "btw_code_id": None,
    "regeltype": "netto",
    "netto_id": None,
    "created_at": "2024-01-15T10:00:00Z",
}

BOEKING_REGEL2 = {
    "id": 102,
    "boeking_id": 100,
    "grootboekrekening_id": 31,
    "omschrijving": "Contra",
    "bedrag": 10000,
    "btw_code_id": None,
    "regeltype": "netto",
    "netto_id": None,
    "created_at": "2024-01-15T10:00:00Z",
}

BOEKING = {
    "id": 100,
    "dagboek_id": 20,
    "boekjaar_id": 10,
    "datum": "2024-01-15",
    "omschrijving": "Test boeking",
    "stuknummer": None,
    "status": "concept",
    "tegenpartij_naam": None,
    "tegenpartij_iban": None,
    "referentie_import": None,
    "import_hash": None,
    "auto_geboekt": False,
    "gecontroleerd": False,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
}

BOEKING_MET_REGELS = {
    "boeking": BOEKING,
    "regels": [BOEKING_REGEL, BOEKING_REGEL2],
}

BTW_CODE = {
    "id": 50,
    "administratie_id": 1,
    "code": "V21",
    "omschrijving": "Verkoop (21%)",
    "percentage": "21",
    "soort": "verkopen_nl_hoog",
    "output_rekening_id": None,
    "input_rekening_id": None,
    "pct_aftrek": "100",
    "actief": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}


@pytest.fixture
def mocked_responses():
    """Activate the ``responses`` mock library for the duration of the test."""
    with resp_lib.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client(mocked_responses):
    """Return a logged-in MboekClient with mocked HTTP."""
    mocked_responses.add(
        resp_lib.POST,
        f"{BASE_URL}/api/auth/login",
        json=LOGIN_RESPONSE,
        status=200,
    )
    c = MboekClient(BASE_URL, "admin", "geheim")
    return c
