"""BTW-aangifte (VAT return) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class RubriekBedragen:
    """Amounts for a single VAT return rubriek.

    Attributes:
        grondslag: Tax base (net amount) in euros.
        btw: VAT amount in euros.
    """

    grondslag: Decimal
    btw: Decimal


@dataclass
class BtwBerekening:
    """Full VAT return calculation, broken down per official rubriek.

    The Dutch BTW-aangifte (VAT return form) groups amounts into five sections
    (rubrieken). This object mirrors that structure exactly.

    Attributes:
        r1a: 21% domestic sales.
        r1b: 9% domestic sales.
        r1c: Other rates.
        r1d: Private use.
        r1e: 0%/exempt sales (grondslag only).
        r2a: Reverse-charge services received.
        r3a: Exports outside the EU (grondslag only).
        r3b: Intra-EU deliveries (grondslag only).
        r3c: Installation/distance sales (grondslag only).
        r4a: Services provided outside the EU.
        r4b: Services provided inside the EU.
        r5a: Total VAT due (floored to whole euros).
        r5b: Input VAT (pre-tax/voorbelasting, ceiled to whole euros).
        r5g: Net payable (5a − 5b); positive = te betalen, negative = te ontvangen.
    """

    r1a: RubriekBedragen
    r1b: RubriekBedragen
    r1c: RubriekBedragen
    r1d: RubriekBedragen
    r1e: RubriekBedragen
    r2a: RubriekBedragen
    r3a: RubriekBedragen
    r3b: RubriekBedragen
    r3c: RubriekBedragen
    r4a: RubriekBedragen
    r4b: RubriekBedragen
    r5a: Decimal
    r5b: Decimal
    r5g: Decimal


@dataclass
class BtwAangifte:
    """A quarterly BTW-aangifte (VAT return).

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        boekjaar_id: ID of the fiscal year this aangifte covers.
        kwartaal: Quarter number (1–4).
        periode_start: First day of the quarter.
        periode_eind: Last day of the quarter.
        berekening: Full per-rubriek breakdown.
        r5g: Net payable amount (positive = te betalen, negative = te ontvangen).
        status: ``concept`` (can be recalculated) or ``definitief`` (locked).
    """

    id: int
    administratie_id: int
    boekjaar_id: int
    kwartaal: int
    periode_start: date
    periode_eind: date
    berekening: BtwBerekening
    r5g: Decimal
    status: str
