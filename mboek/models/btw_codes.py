"""BTW (VAT) code models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mboek.models._enums import BtwSoort


@dataclass
class BtwCode:
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

    def __post_init__(self) -> None:
        if self.percentage < 0:
            raise ValueError(f"percentage must be >= 0, got {self.percentage}")
        if not (0 <= self.pct_aftrek <= 100):
            raise ValueError(
                f"pct_aftrek must be between 0 and 100, got {self.pct_aftrek}"
            )
