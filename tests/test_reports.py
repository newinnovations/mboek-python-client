"""Tests for the reports resource."""

from __future__ import annotations

from decimal import Decimal

import responses

from tests.conftest import BASE_URL

BALANS_RESPONSE = {
    "boekjaar_naam": "2024",
    "activa": [
        {
            "code": "1220",
            "naam": "Bank",
            "debet": "5000.00",
            "credit": "0.00",
            "saldo": "5000.00",
        }
    ],
    "passiva": [
        {
            "code": "2000",
            "naam": "Eigen vermogen",
            "debet": "0.00",
            "credit": "5000.00",
            "saldo": "5000.00",
        }
    ],
    "totaal_activa": "5000.00",
    "totaal_passiva": "5000.00",
    "in_balans": True,
}

WV_RESPONSE = {
    "boekjaar_naam": "2024",
    "opbrengsten": [{"code": "3000", "naam": "Omzet", "bedrag": "10000.00"}],
    "kosten": [{"code": "4000", "naam": "Kosten", "bedrag": "6000.00"}],
    "bijzonder": [],
    "totaal_opbrengsten": "10000.00",
    "totaal_kosten": "6000.00",
    "totaal_bijzonder": "0.00",
    "netto_resultaat": "4000.00",
}


def test_balans(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/rapporten/balans",
        json=BALANS_RESPONSE,
    )
    report = client.administratie(1).boekjaar(10).reports.balans()
    assert report.boekjaar_naam == "2024"
    assert report.in_balans is True
    assert report.totaal_activa == Decimal("5000.00")
    assert len(report.activa) == 1
    assert report.activa[0].saldo == Decimal("5000.00")


def test_winst_verlies(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/1/rapporten/winst-verlies",
        json=WV_RESPONSE,
    )
    report = client.administratie(1).boekjaar(10).reports.winst_verlies()
    assert report.netto_resultaat == Decimal("4000.00")
    assert len(report.opbrengsten) == 1
    assert report.opbrengsten[0].bedrag == Decimal("10000.00")
