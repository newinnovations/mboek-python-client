"""Automatic booking rule models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mboek.models._enums import AutoBookingActieType, AutoBookingBedragType


@dataclass
class AutoBookingRuleLine:
    """A single line (action) of an automatic booking rule.

    Attributes:
        id: Unique database identifier.
        rule_id: ID of the parent rule.
        tegenrekening_id: The contra account to book to.
        btw_code_id: Optional BTW code to apply.
        omschrijving: Optional line description override.
        bedrag_type: ``vast`` (fixed amount) or ``rest`` (remainder).
        bedrag: Fixed amount in euros (only applicable when ``bedrag_type == "vast"``).
    """

    id: int
    rule_id: int
    tegenrekening_id: int
    btw_code_id: int | None
    omschrijving: str | None
    bedrag_type: AutoBookingBedragType
    bedrag: Decimal | None


@dataclass
class AutoBookingRule:
    """An automatic booking rule.

    Rules are evaluated in priority order (lowest number first). The first rule
    whose conditions match a boeking is applied.

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        naam: Human-readable name.
        prioriteit: Sort priority (lower = evaluated first).
        actief: Whether the rule is enabled.
        actie_type: ``enkel`` (single contra account) or ``splits`` (multiple accounts).
        btw_code_id: Optional BTW code for simple ``enkel`` rules.
        iban_eigen: Regex matched against the dagboek's own IBAN.
        iban_tegenpartij: Regex matched against the counterparty IBAN.
        omschrijving_regex: Regex matched against the transaction description.
        tegenrekening_id: Optional contra account for simple ``enkel`` rules.
        lines: The action lines to execute when the rule matches.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    administratie_id: int
    naam: str
    prioriteit: int
    actief: bool
    actie_type: AutoBookingActieType
    btw_code_id: int | None
    iban_eigen: str | None
    iban_tegenpartij: str | None
    omschrijving_regex: str | None
    tegenrekening_id: int | None
    lines: list[AutoBookingRuleLine]
    created_at: datetime
    updated_at: datetime


@dataclass
class NewAutoBookingRuleLine:
    """A line for a new or updated automatic booking rule.

    Exactly one of ``tegenrekening_id``, ``tegenrekening_naam``, or
    ``tegenrekening_code`` must be provided.  When a name or code is
    supplied the resource layer resolves it to an ID before sending the request.

    Attributes:
        bedrag_type: ``vast`` or ``rest``.
        tegenrekening_id: Contra account (numeric ID).
        tegenrekening_naam: Account name — alternative to ``tegenrekening_id``.
        tegenrekening_code: Account code — alternative to ``tegenrekening_id``.
        btw_code_id: Optional BTW code.
        omschrijving: Optional description override.
        bedrag: Fixed amount in euros (required when ``bedrag_type == "vast"``).
    """

    bedrag_type: AutoBookingBedragType = AutoBookingBedragType.REST
    tegenrekening_id: int | None = None
    tegenrekening_naam: str | None = None
    tegenrekening_code: str | None = None
    btw_code_id: int | None = None
    omschrijving: str | None = None
    bedrag: Decimal | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.tegenrekening_id,
                self.tegenrekening_naam,
                self.tegenrekening_code,
            ]
        )
        if provided == 0:
            raise ValueError(
                "Provide exactly one of: tegenrekening_id, tegenrekening_naam, tegenrekening_code"
            )
        if provided > 1:
            raise ValueError(
                "Provide only one of: tegenrekening_id, tegenrekening_naam, tegenrekening_code"
            )
        if self.bedrag_type == AutoBookingBedragType.VAST and self.bedrag is None:
            raise ValueError("bedrag is required when bedrag_type is 'vast'")

    def to_dict(self, *, tegenrekening_id: int | None = None) -> dict:
        resolved_tegenrekening_id = (
            self.tegenrekening_id if tegenrekening_id is None else tegenrekening_id
        )
        if resolved_tegenrekening_id is None:
            raise ValueError(
                "tegenrekening_id is not yet resolved; the resource should have resolved "
                "tegenrekening_naam / tegenrekening_code before calling to_dict()"
            )
        d: dict = {
            "tegenrekening_id": resolved_tegenrekening_id,
            "bedrag_type": self.bedrag_type.value,
        }
        if self.btw_code_id is not None:
            d["btw_code_id"] = self.btw_code_id
        if self.omschrijving is not None:
            d["omschrijving"] = self.omschrijving
        if self.bedrag is not None:
            from decimal import ROUND_DOWN, Decimal

            quantized = self.bedrag.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            if quantized != self.bedrag:
                raise ValueError(f"bedrag {self.bedrag} has more than 2 decimal places")
            d["bedrag"] = str(quantized)
        return d
