"""Automatic booking rule models."""

from __future__ import annotations

from dataclasses import dataclass, field
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
class CreateAutoBookingRuleLineInput:
    """A line for a new or updated automatic booking rule.

    Attributes:
        grootboekrekening_id: Contra account.
        btw_code_id: Optional BTW code.
        omschrijving: Optional description override.
        bedrag_type: ``vast`` or ``rest``.
        bedrag: Fixed amount in euros (required when ``bedrag_type == "vast"``).
    """

    grootboekrekening_id: int
    bedrag_type: AutoBookingBedragType = AutoBookingBedragType.REST
    btw_code_id: int | None = None
    omschrijving: str | None = None
    bedrag: Decimal | None = None

    def to_dict(self) -> dict:
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


@dataclass
class CreateAutoBookingRuleInput:
    """Input for creating a new automatic booking rule.

    Attributes:
        naam: Human-readable name.
        actie_type: Action type.
        lines: One or more action lines.
        prioriteit: Sort priority (default 100).
        actief: Enable the rule (default ``True``).
        eigen_iban_patroon: Regex for own IBAN matching.
        tegenpartij_iban_patroon: Regex for counterparty IBAN matching.
        omschrijving_patroon: Regex for transaction description matching.
    """

    naam: str
    actie_type: AutoBookingActieType
    lines: list[CreateAutoBookingRuleLineInput]
    prioriteit: int = 100
    actief: bool = True
    eigen_iban_patroon: str | None = None
    tegenpartij_iban_patroon: str | None = None
    omschrijving_patroon: str | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "naam": self.naam,
            "actie_type": self.actie_type.value,
            "lines": [ln.to_dict() for ln in self.lines],
            "prioriteit": self.prioriteit,
            "actief": self.actief,
        }
        if self.eigen_iban_patroon is not None:
            d["eigen_iban_patroon"] = self.eigen_iban_patroon
        if self.tegenpartij_iban_patroon is not None:
            d["tegenpartij_iban_patroon"] = self.tegenpartij_iban_patroon
        if self.omschrijving_patroon is not None:
            d["omschrijving_patroon"] = self.omschrijving_patroon
        return d


@dataclass
class UpdateAutoBookingRuleInput:
    """Input for partially updating an automatic booking rule.

    All fields optional. If ``lines`` is provided the existing lines are
    replaced atomically.
    """

    naam: str | None = None
    prioriteit: int | None = None
    actief: bool | None = None
    actie_type: AutoBookingActieType | None = None
    eigen_iban_patroon: str | None = None
    tegenpartij_iban_patroon: str | None = None
    omschrijving_patroon: str | None = None
    lines: list[CreateAutoBookingRuleLineInput] | None = field(default=None)

    def to_dict(self) -> dict:
        d: dict = {}
        if self.naam is not None:
            d["naam"] = self.naam
        if self.prioriteit is not None:
            d["prioriteit"] = self.prioriteit
        if self.actief is not None:
            d["actief"] = self.actief
        if self.actie_type is not None:
            d["actie_type"] = self.actie_type.value
        if self.eigen_iban_patroon is not None:
            d["eigen_iban_patroon"] = self.eigen_iban_patroon
        if self.tegenpartij_iban_patroon is not None:
            d["tegenpartij_iban_patroon"] = self.tegenpartij_iban_patroon
        if self.omschrijving_patroon is not None:
            d["omschrijving_patroon"] = self.omschrijving_patroon
        if self.lines is not None:
            d["lines"] = [ln.to_dict() for ln in self.lines]
        return d
