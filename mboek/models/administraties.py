"""Administratie (company administration) models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AdministratieResponse:
    """A company administration owned by the authenticated user.

    Attributes:
        id: Unique database identifier.
        naam: Name of the administration (e.g. company name).
        beschrijving: Optional description.
        kvk_nummer: Dutch Chamber of Commerce registration number.
        btw_nummer: VAT registration number (e.g. ``NL123456789B01``).
        adres: Postal address.
        active: Whether the administration is active.
        huidig_boekjaar_id: ID of the currently selected fiscal year.
        bankimport_rekening_id: ID of the staging account used for bank imports (9990).
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    naam: str
    beschrijving: str | None
    kvk_nummer: str | None
    btw_nummer: str | None
    adres: str | None
    active: bool
    huidig_boekjaar_id: int | None
    bankimport_rekening_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass
class NewAdministratie:
    """Input for creating a new administratie.

    Attributes:
        naam: Name of the administration (required).
        beschrijving: Optional description.
        kvk_nummer: Optional KvK registration number.
        btw_nummer: Optional VAT registration number.
        adres: Optional postal address.
    """

    naam: str
    beschrijving: str | None = None
    kvk_nummer: str | None = None
    btw_nummer: str | None = None
    adres: str | None = None

    def to_dict(self) -> dict:
        return {
            k: v
            for k, v in {
                "naam": self.naam,
                "beschrijving": self.beschrijving,
                "kvk_nummer": self.kvk_nummer,
                "btw_nummer": self.btw_nummer,
                "adres": self.adres,
            }.items()
            if v is not None
        }


@dataclass
class UpdateAdministratie:
    """Input for partially updating an administratie.

    All fields are optional — omit any field you do not want to change.
    Pass ``None`` explicitly to clear a nullable field.

    Attributes:
        naam: New name.
        beschrijving: New description (``None`` clears the field).
        kvk_nummer: New KvK number (``None`` clears the field).
        btw_nummer: New BTW number (``None`` clears the field).
        adres: New address (``None`` clears the field).
        active: Set active/inactive.
        huidig_boekjaar_id: Set the default boekjaar.
    """

    naam: str | None = field(default=None)
    beschrijving: str | None = field(default=None)
    kvk_nummer: str | None = field(default=None)
    btw_nummer: str | None = field(default=None)
    adres: str | None = field(default=None)
    active: bool | None = field(default=None)
    huidig_boekjaar_id: int | None = field(default=None)

    def to_dict(self) -> dict:
        d: dict = {}
        if self.naam is not None:
            d["naam"] = self.naam
        if self.active is not None:
            d["active"] = self.active
        if self.huidig_boekjaar_id is not None:
            d["huidig_boekjaar_id"] = self.huidig_boekjaar_id
        for key in ("beschrijving", "kvk_nummer", "btw_nummer", "adres"):
            val = getattr(self, key)
            if val is not None:
                d[key] = val
        return d
