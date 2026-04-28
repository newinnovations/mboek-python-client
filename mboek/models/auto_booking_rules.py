"""Automatic booking rule models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mboek.models._enums import AutoBookingActieType, AutoBookingBedragType


@dataclass
class AutoBookingRuleLineResponse:
    """A single line (action) of an automatic booking rule.

    Attributes:
        id: Unique database identifier.
        rule_id: ID of the parent rule.
        volgorde: Sort order within the rule.
        grootboekrekening_id: The contra account to book to.
        btw_code_id: Optional BTW code to apply.
        omschrijving: Optional line description override.
        bedrag_type: ``vast`` (fixed amount) or ``rest`` (remainder).
        bedrag: Fixed amount in euros (only applicable when ``bedrag_type == "vast"``).
    """

    id: int
    rule_id: int
    volgorde: int
    grootboekrekening_id: int
    btw_code_id: int | None
    omschrijving: str | None
    bedrag_type: AutoBookingBedragType
    bedrag: Decimal | None


@dataclass
class AutoBookingRuleResponse:
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
        eigen_iban_patroon: Regex matched against the dagboek's own IBAN.
        tegenpartij_iban_patroon: Regex matched against the counterparty IBAN.
        omschrijving_patroon: Regex matched against the transaction description.
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
    eigen_iban_patroon: str | None
    tegenpartij_iban_patroon: str | None
    omschrijving_patroon: str | None
    lines: list[AutoBookingRuleLineResponse]
    created_at: datetime
    updated_at: datetime


@dataclass
class NewAutoBookingRuleLine:
    """A line for a new or updated automatic booking rule.

    Exactly one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
    ``grootboekrekening_code`` must be provided.  When a name or code is
    supplied the resource layer resolves it to an ID before sending the request.

    Attributes:
        bedrag_type: ``vast`` or ``rest``.
        grootboekrekening_id: Contra account (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        btw_code_id: Optional BTW code.
        omschrijving: Optional description override.
        bedrag: Fixed amount in euros (required when ``bedrag_type == "vast"``).
    """

    bedrag_type: AutoBookingBedragType = AutoBookingBedragType.REST
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    btw_code_id: int | None = None
    omschrijving: str | None = None
    bedrag: Decimal | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided == 0:
            raise ValueError(
                "Provide exactly one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        if self.grootboekrekening_id is None:
            raise ValueError(
                "grootboekrekening_id is not yet resolved; the resource should have resolved "
                "grootboekrekening_naam / grootboekrekening_code before calling to_dict()"
            )
        d: dict = {
            "grootboekrekening_id": self.grootboekrekening_id,
            "bedrag_type": self.bedrag_type.value,
        }
        if self.btw_code_id is not None:
            d["btw_code_id"] = self.btw_code_id
        if self.omschrijving is not None:
            d["omschrijving"] = self.omschrijving
        if self.bedrag is not None:
            d["bedrag"] = str(self.bedrag)
        return d
