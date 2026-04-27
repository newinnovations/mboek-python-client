"""BTW (VAT) code models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mboek.models._enums import BtwSoort


@dataclass
class BtwCodeResponse:
    """A BTW (VAT) code configuration.

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        code: Short code (e.g. ``"V21"`` for 21% sales VAT).
        omschrijving: Description (e.g. ``"Verkoop (21%)"``.
        percentage: VAT rate as a decimal percentage (e.g. ``Decimal("21")``).
        soort: VAT type, determines the Dutch tax return rubriek.
        output_rekening_id: Linked "BTW te betalen" account.
        input_rekening_id: Linked "BTW te vorderen" account.
        pct_aftrek: Deductibility percentage (0–100; typically 100).
        actief: Whether this code is active for new bookings.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    administratie_id: int
    code: str
    omschrijving: str
    percentage: Decimal
    soort: BtwSoort
    output_rekening_id: int | None
    input_rekening_id: int | None
    pct_aftrek: Decimal
    actief: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateBtwCodeInput:
    """Input for creating a new BTW code.

    Attributes:
        code: Short code (must be unique within the administratie).
        omschrijving: Description.
        percentage: VAT rate as a percentage (e.g. ``Decimal("21")``).
        soort: VAT type.
        output_rekening_id: Linked "BTW te betalen" account.
        input_rekening_id: Linked "BTW te vorderen" account.
        pct_aftrek: Deductibility percentage (defaults to 100).
    """

    code: str
    omschrijving: str
    percentage: Decimal
    soort: BtwSoort
    output_rekening_id: int | None = None
    input_rekening_id: int | None = None
    pct_aftrek: Decimal | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "code": self.code,
            "omschrijving": self.omschrijving,
            "percentage": str(self.percentage),
            "soort": self.soort.value,
        }
        if self.output_rekening_id is not None:
            d["output_rekening_id"] = self.output_rekening_id
        if self.input_rekening_id is not None:
            d["input_rekening_id"] = self.input_rekening_id
        if self.pct_aftrek is not None:
            d["pct_aftrek"] = str(self.pct_aftrek)
        return d


@dataclass
class UpdateBtwCodeInput:
    """Input for partially updating a BTW code.

    All fields optional.

    Attributes:
        code: New short code.
        omschrijving: New description.
        percentage: New VAT rate.
        soort: New VAT type.
        output_rekening_id: New "BTW te betalen" account.
        input_rekening_id: New "BTW te vorderen" account.
        pct_aftrek: New deductibility percentage.
        actief: Enable or disable this code.
    """

    code: str | None = None
    omschrijving: str | None = None
    percentage: Decimal | None = None
    soort: BtwSoort | None = None
    output_rekening_id: int | None = None
    input_rekening_id: int | None = None
    pct_aftrek: Decimal | None = None
    actief: bool | None = None

    def to_dict(self) -> dict:
        d: dict = {}
        if self.code is not None:
            d["code"] = self.code
        if self.omschrijving is not None:
            d["omschrijving"] = self.omschrijving
        if self.percentage is not None:
            d["percentage"] = str(self.percentage)
        if self.soort is not None:
            d["soort"] = self.soort.value
        if self.output_rekening_id is not None:
            d["output_rekening_id"] = self.output_rekening_id
        if self.input_rekening_id is not None:
            d["input_rekening_id"] = self.input_rekening_id
        if self.pct_aftrek is not None:
            d["pct_aftrek"] = str(self.pct_aftrek)
        if self.actief is not None:
            d["actief"] = self.actief
        return d
