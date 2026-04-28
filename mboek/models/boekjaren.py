"""Boekjaar (fiscal year) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from mboek.models._enums import BoekjaarStatus


@dataclass
class Boekjaar:
    """A fiscal year belonging to an administratie.

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        naam: Display name (e.g. ``"2024"``).
        start_datum: First day of the fiscal year.
        eind_datum: Last day of the fiscal year.
        status: ``open`` (accepting new boekingen) or ``gesloten`` (locked).
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    administratie_id: int
    naam: str
    start_datum: date
    eind_datum: date
    status: BoekjaarStatus
    created_at: datetime
    updated_at: datetime


# Keep a type alias consistent with response naming used in other modules.
BoekjaarResponse = Boekjaar


@dataclass
class NewBoekjaar:
    """Input for creating a new boekjaar.

    Attributes:
        naam: Display name (e.g. ``"2024"``).
        start_datum: First day of the fiscal year (``YYYY-MM-DD``).
        eind_datum: Last day of the fiscal year (``YYYY-MM-DD``).
    """

    naam: str
    start_datum: date
    eind_datum: date

    def to_dict(self) -> dict:
        return {
            "naam": self.naam,
            "start_datum": self.start_datum.isoformat(),
            "eind_datum": self.eind_datum.isoformat(),
        }


@dataclass
class UpdateBoekjaar:
    """Input for partially updating a boekjaar.

    All fields optional. Do **not** use this to close/reopen a boekjaar —
    use the dedicated :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.afsluiten`
    and :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.heropenen` methods.

    Attributes:
        naam: New display name.
        start_datum: New start date.
        eind_datum: New end date.
    """

    naam: str | None = None
    start_datum: date | None = None
    eind_datum: date | None = None

    def to_dict(self) -> dict:
        d: dict = {}
        if self.naam is not None:
            d["naam"] = self.naam
        if self.start_datum is not None:
            d["start_datum"] = self.start_datum.isoformat()
        if self.eind_datum is not None:
            d["eind_datum"] = self.eind_datum.isoformat()
        return d
