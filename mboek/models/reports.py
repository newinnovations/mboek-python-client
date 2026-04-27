"""Financial report models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BalansRegel:
    """A single account line in the balance sheet.

    Attributes:
        code: Account code.
        naam: Account name.
        debet: Debit total in euros.
        credit: Credit total in euros.
        saldo: Net balance in euros (positive = asset / equity perspective).
    """

    code: str
    naam: str
    debet: Decimal
    credit: Decimal
    saldo: Decimal


@dataclass
class BalansReport:
    """Balance sheet (balans) for a fiscal year.

    Attributes:
        boekjaar_naam: Name of the fiscal year.
        activa: Asset account lines.
        passiva: Liability and equity account lines.
        totaal_activa: Total assets in euros.
        totaal_passiva: Total liabilities + equity in euros.
        in_balans: ``True`` when the difference between activa and passiva is < €0.01.
    """

    boekjaar_naam: str
    activa: list[BalansRegel]
    passiva: list[BalansRegel]
    totaal_activa: Decimal
    totaal_passiva: Decimal
    in_balans: bool


@dataclass
class WinstVerliesRegel:
    """A single account line in the profit-and-loss statement.

    Attributes:
        code: Account code.
        naam: Account name.
        bedrag: Amount in euros (positive = cost / revenue as appropriate for the type).
    """

    code: str
    naam: str
    bedrag: Decimal


@dataclass
class WinstVerliesReport:
    """Profit-and-loss report (winst & verlies) for a fiscal year.

    Attributes:
        boekjaar_naam: Name of the fiscal year.
        opbrengsten: Revenue lines.
        kosten: Cost lines.
        bijzonder: Extraordinary items.
        totaal_opbrengsten: Total revenues in euros.
        totaal_kosten: Total costs in euros.
        totaal_bijzonder: Total extraordinary items in euros.
        netto_resultaat: Net result (opbrengsten − kosten − bijzonder) in euros.
    """

    boekjaar_naam: str
    opbrengsten: list[WinstVerliesRegel]
    kosten: list[WinstVerliesRegel]
    bijzonder: list[WinstVerliesRegel]
    totaal_opbrengsten: Decimal
    totaal_kosten: Decimal
    totaal_bijzonder: Decimal
    netto_resultaat: Decimal
