"""Dagboek (journal / sub-ledger) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mboek.models._enums import DagboekType


@dataclass
class DagboekResponse:
    """A dagboek (journal / sub-ledger) belonging to an administratie.

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        code: Short alphanumeric code (e.g. ``"BANK"``).
        naam: Display name.
        dagboek_type: One of ``bank``, ``kas``, ``inkoop``, ``verkoop``, ``memoriaal``.
        grootboekrekening_id: Linked grootboekrekening (e.g. the bank balance account).
        iban: IBAN number of the linked bank account, used for auto-matching during import.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    administratie_id: int
    code: str
    naam: str
    dagboek_type: DagboekType
    grootboekrekening_id: int | None
    iban: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DagboekWerkStatus:
    """Work-status counts for a dagboek.

    Attributes:
        dagboek_id: ID of the dagboek.
        onverwerkt: Number of boekingen still pointing at the bankimport staging account.
        te_bevestigen: Number of auto-booked entries not yet manually confirmed.
    """

    dagboek_id: int
    onverwerkt: int
    te_bevestigen: int


@dataclass
class NewDagboek:
    """Input for creating a new dagboek.

    At most one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
    ``grootboekrekening_code`` may be provided.  When a name or code is supplied
    the resource layer resolves it to an ID before sending the request.

    Attributes:
        code: Short code (e.g. ``"BANK"``).
        naam: Display name.
        dagboek_type: Journal type.
        grootboekrekening_id: Optional linked balance account (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        iban: Optional IBAN for bank-statement auto-matching.
    """

    code: str
    naam: str
    dagboek_type: DagboekType
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    iban: str | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        d: dict = {
            "code": self.code,
            "naam": self.naam,
            "dagboek_type": self.dagboek_type.value,
        }
        if self.grootboekrekening_id is not None:
            d["grootboekrekening_id"] = self.grootboekrekening_id
        if self.iban is not None:
            d["iban"] = self.iban
        return d


@dataclass
class UpdateDagboek:
    """Input for partially updating a dagboek.

    All fields optional.  At most one of ``grootboekrekening_id``,
    ``grootboekrekening_naam``, or ``grootboekrekening_code`` may be provided.
    When a name or code is supplied the resource layer resolves it to an ID
    before sending the request.

    Attributes:
        code: New short code.
        naam: New display name.
        dagboek_type: New journal type.
        grootboekrekening_id: New linked balance account (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        iban: New IBAN.
    """

    code: str | None = None
    naam: str | None = None
    dagboek_type: DagboekType | None = None
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    iban: str | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.code is not None:
            d["code"] = self.code
        if self.naam is not None:
            d["naam"] = self.naam
        if self.dagboek_type is not None:
            d["dagboek_type"] = self.dagboek_type.value
        if self.grootboekrekening_id is not None:
            d["grootboekrekening_id"] = self.grootboekrekening_id
        if self.iban is not None:
            d["iban"] = self.iban
        return d
