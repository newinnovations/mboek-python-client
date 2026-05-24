"""Administratie (company administration) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Administratie:
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
