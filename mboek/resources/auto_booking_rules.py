"""Automatic booking rules resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from mboek._parsers import parse_auto_booking_rule, parse_boeking_met_regels
from mboek.models._enums import AutoBookingActieType
from mboek.models.auto_booking_rules import AutoBookingRule
from mboek.models.boekingen import Boeking
from mboek.resources._base import BaseResource

if TYPE_CHECKING:
    from mboek.models.auto_booking_rules import NewAutoBookingRuleLine


class AutoBookingRulesResource(BaseResource):
    """CRUD + execution operations for automatic booking rules.

    Instantiated via :py:meth:`AdministratieScope.auto_booking_rules`.

    Rules are evaluated in ascending priority order; the first match wins.
    Each rule matches on:

    - ``eigen_iban_patroon`` — regex on the dagboek's own IBAN
    - ``tegenpartij_iban_patroon`` — regex on the counterparty IBAN
    - ``omschrijving_patroon`` — regex on the transaction description

    Actions:

    - ``enkel`` — assign one contra account (+ optional BTW code)
    - ``splits`` — distribute across multiple contra accounts
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(
        self, *, limit: int | None = None, offset: int | None = None
    ) -> builtins.list[AutoBookingRule]:
        """Return all automatic booking rules for the administratie.

        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically.

        Returns:
            List sorted by priority ascending, then name.
        """
        return [
            parse_auto_booking_rule(d)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/regels",
                limit=limit,
                offset=offset,
            )
        ]

    def create(
        self,
        naam: str,
        actie_type: AutoBookingActieType,
        lines: "builtins.list[NewAutoBookingRuleLine]",
        *,
        prioriteit: int = 100,
        actief: bool = True,
        eigen_iban_patroon: str | None = None,
        tegenpartij_iban_patroon: str | None = None,
        omschrijving_patroon: str | None = None,
    ) -> AutoBookingRule:
        """Create a new automatic booking rule.

        Rule lines may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        IDs are resolved automatically.

        Args:
            naam: Human-readable name.
            actie_type: Action type (``enkel`` or ``splits``).
            lines: One or more action lines.
            prioriteit: Sort priority (lower = evaluated first, default 100).
            actief: Enable the rule (default ``True``).
            eigen_iban_patroon: Regex for own IBAN matching.
            tegenpartij_iban_patroon: Regex for counterparty IBAN matching.
            omschrijving_patroon: Regex for transaction description matching.
        """
        self._resolve_lines(lines)
        data: dict = {
            "naam": naam,
            "actie_type": actie_type.value,
            "lines": [ln.to_dict() for ln in lines],
            "prioriteit": prioriteit,
            "actief": actief,
        }
        if eigen_iban_patroon is not None:
            data["eigen_iban_patroon"] = eigen_iban_patroon
        if tegenpartij_iban_patroon is not None:
            data["tegenpartij_iban_patroon"] = tegenpartij_iban_patroon
        if omschrijving_patroon is not None:
            data["omschrijving_patroon"] = omschrijving_patroon
        return parse_auto_booking_rule(
            self._post(f"/api/administraties/{self._admin_id}/regels", json=data)
        )

    def update(
        self,
        rule_id: int,
        *,
        naam: str | None = None,
        prioriteit: int | None = None,
        actief: bool | None = None,
        actie_type: AutoBookingActieType | None = None,
        eigen_iban_patroon: str | None = None,
        tegenpartij_iban_patroon: str | None = None,
        omschrijving_patroon: str | None = None,
        lines: "builtins.list[NewAutoBookingRuleLine] | None" = None,
    ) -> AutoBookingRule:
        """Partially update a rule.

        Rule lines may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        IDs are resolved automatically.

        Args:
            rule_id: Rule ID.
            naam: New name.
            prioriteit: New sort priority.
            actief: Enable or disable the rule.
            actie_type: New action type.
            eigen_iban_patroon: New regex for own IBAN matching.
            tegenpartij_iban_patroon: New regex for counterparty IBAN matching.
            omschrijving_patroon: New regex for description matching.
            lines: Full replacement set of action lines.
        """
        if lines is not None:
            self._resolve_lines(lines)
        data: dict = {}
        if naam is not None:
            data["naam"] = naam
        if prioriteit is not None:
            data["prioriteit"] = prioriteit
        if actief is not None:
            data["actief"] = actief
        if actie_type is not None:
            data["actie_type"] = actie_type.value
        if eigen_iban_patroon is not None:
            data["eigen_iban_patroon"] = eigen_iban_patroon
        if tegenpartij_iban_patroon is not None:
            data["tegenpartij_iban_patroon"] = tegenpartij_iban_patroon
        if omschrijving_patroon is not None:
            data["omschrijving_patroon"] = omschrijving_patroon
        if lines is not None:
            data["lines"] = [ln.to_dict() for ln in lines]
        return parse_auto_booking_rule(
            self._patch(
                f"/api/administraties/{self._admin_id}/regels/{rule_id}", json=data
            )
        )

    def _resolve_lines(self, lines: "builtins.list[NewAutoBookingRuleLine]") -> None:
        """Resolve grootboekrekening naam/code → id for each line in-place."""
        for line in lines:
            if line.grootboekrekening_id is None:
                line.grootboekrekening_id = self._resolve_rekening_id(
                    self._admin_id,
                    naam=line.grootboekrekening_naam,
                    code=line.grootboekrekening_code,
                )

    def delete(self, rule_id: int) -> None:
        """Permanently delete a rule.

        Args:
            rule_id: Rule ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/regels/{rule_id}")

    def apply_to_boeking(self, boeking_id: int) -> Boeking | None:
        """Apply the first matching rule to a single boeking.

        Args:
            boeking_id: Boeking ID.

        Returns:
            The updated boeking, or ``None`` if no rule matched.
        """
        data = self._post(
            f"/api/administraties/{self._admin_id}/boekingen/{boeking_id}/apply-rules"
        )
        if data:
            return parse_boeking_met_regels(data)
        return None
