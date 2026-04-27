"""Grootboekrekening (chart of accounts) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mboek.models._enums import RekeningCategorie, RekeningType


@dataclass
class GrootboekrekeningResponse:
    """A general-ledger account (grootboekrekening).

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        code: Account code (e.g. ``"1220"``).
        naam: Account name (e.g. ``"Bank"``).
        rekening_type: Account type (activa / passiva / kosten / opbrengsten / bijzonder).
        categorie: Statement category (balans / winstverlies).
        rgs_code: Optional Dutch RGS (Referentie Grootboekschema) code.
        parent_id: Optional ID of a parent account for hierarchical charts.
        default_btw_id: Default BTW code applied automatically when booking to this account.
        actief: Whether this account is active (inactive accounts are hidden in most views).
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    administratie_id: int
    code: str
    naam: str
    rekening_type: RekeningType
    categorie: RekeningCategorie
    rgs_code: str | None
    parent_id: int | None
    default_btw_id: int | None
    actief: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class GrootboekrekeningMetSaldoResponse:
    """A grootboekrekening enriched with transaction count and net balance.

    Attributes:
        rekening: The underlying account details.
        aantal_transacties: Number of boekingsregels in the boekjaar.
        saldo: Net balance in euros (positive = debet).
    """

    rekening: GrootboekrekeningResponse
    aantal_transacties: int
    saldo: Decimal


@dataclass
class GrootboekMutatie:
    """A single mutation (boekingsregel) in the account ledger.

    Attributes:
        regel_id: ID of the boekingsregel.
        boeking_id: ID of the parent boeking.
        dagboek_id: ID of the dagboek.
        datum: Booking date.
        dagboek_code: Short code of the dagboek (e.g. ``"BANK"``).
        dagboek_naam: Name of the dagboek.
        boeking_omschrijving: Description of the parent boeking.
        regel_omschrijving: Description of this specific regel.
        bedrag: Amount in euros (positive = debet, negative = credit).
    """

    regel_id: int
    boeking_id: int
    dagboek_id: int
    datum: str
    dagboek_code: str
    dagboek_naam: str
    boeking_omschrijving: str
    regel_omschrijving: str
    bedrag: Decimal


@dataclass
class CreateGrootboekrekeningInput:
    """Input for creating a new grootboekrekening.

    Attributes:
        code: Account code (must be unique within the administratie).
        naam: Account name.
        rekening_type: Account type.
        categorie: Statement category.
        rgs_code: Optional RGS code.
        parent_id: Optional parent account ID.
        default_btw_id: Optional default BTW code.
    """

    code: str
    naam: str
    rekening_type: RekeningType
    categorie: RekeningCategorie
    rgs_code: str | None = None
    parent_id: int | None = None
    default_btw_id: int | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "code": self.code,
            "naam": self.naam,
            "rekening_type": self.rekening_type.value,
            "categorie": self.categorie.value,
        }
        if self.rgs_code is not None:
            d["rgs_code"] = self.rgs_code
        if self.parent_id is not None:
            d["parent_id"] = self.parent_id
        if self.default_btw_id is not None:
            d["default_btw_id"] = self.default_btw_id
        return d


@dataclass
class UpdateGrootboekrekeningInput:
    """Input for partially updating a grootboekrekening.

    All fields optional.

    Attributes:
        code: New account code.
        naam: New account name.
        rekening_type: New account type.
        categorie: New statement category.
        rgs_code: New RGS code.
        parent_id: New parent account ID.
        default_btw_id: New default BTW code.
        actief: Enable or disable the account.
    """

    code: str | None = None
    naam: str | None = None
    rekening_type: RekeningType | None = None
    categorie: RekeningCategorie | None = None
    rgs_code: str | None = None
    parent_id: int | None = None
    default_btw_id: int | None = None
    actief: bool | None = None

    def to_dict(self) -> dict:
        d: dict = {}
        if self.code is not None:
            d["code"] = self.code
        if self.naam is not None:
            d["naam"] = self.naam
        if self.rekening_type is not None:
            d["rekening_type"] = self.rekening_type.value
        if self.categorie is not None:
            d["categorie"] = self.categorie.value
        if self.rgs_code is not None:
            d["rgs_code"] = self.rgs_code
        if self.parent_id is not None:
            d["parent_id"] = self.parent_id
        if self.default_btw_id is not None:
            d["default_btw_id"] = self.default_btw_id
        if self.actief is not None:
            d["actief"] = self.actief
        return d
