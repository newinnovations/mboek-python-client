"""Enum types mirroring the mBoek backend domain enumerations."""

from __future__ import annotations

from enum import Enum


class BoekjaarStatus(str, Enum):
    """Status of a fiscal year (boekjaar)."""

    OPEN = "open"
    GESLOTEN = "gesloten"


class RekeningType(str, Enum):
    """Category of a grootboekrekening (general-ledger account)."""

    ACTIVA = "activa"
    PASSIVA = "passiva"
    KOSTEN = "kosten"
    OPBRENGSTEN = "opbrengsten"
    BIJZONDER = "bijzonder"


class RekeningCategorie(str, Enum):
    """Financial statement category of a rekening."""

    BALANS = "balans"
    WINSTVERLIES = "winstverlies"


class DagboekType(str, Enum):
    """Type of a dagboek (journal / sub-ledger)."""

    BANK = "bank"
    KAS = "kas"
    INKOOP = "inkoop"
    VERKOOP = "verkoop"
    MEMORIAAL = "memoriaal"


class Regeltype(str, Enum):
    """Type of a boekingsregel (journal entry line)."""

    NETTO = "netto"
    BTW = "btw"


class BtwSoort(str, Enum):
    """BTW (VAT) code type, determining the Dutch VAT return rubriek."""

    VERKOPEN_NL_HOOG = "verkopen_nl_hoog"
    VERKOPEN_NL_LAAG = "verkopen_nl_laag"
    VERKOPEN_NL_NUL = "verkopen_nl_nul"
    INKOPEN_NL = "inkopen_nl"
    INKOPEN_EU = "inkopen_eu"
    INKOPEN_INT = "inkopen_int"
    VERLEGD_NL = "verlegd_nl"


class BoekingStatus(str, Enum):
    """Status of a boeking (journal entry)."""

    CONCEPT = "concept"
    DEFINITIEF = "definitief"


class AutoBookingActieType(str, Enum):
    """Action type of an automatic booking rule."""

    ENKEL = "enkel"
    SPLITS = "splits"


class AutoBookingBedragType(str, Enum):
    """Amount type for a split automatic booking rule line."""

    VAST = "vast"
    REST = "rest"


class ImportFormaat(str, Enum):
    """Bank statement file format for import."""

    MT940 = "mt940"
    CAMT053 = "camt053"
