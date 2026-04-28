"""Automatic booking rules resource."""

from __future__ import annotations

from mboek._parsers import parse_auto_booking_rule, parse_boeking_met_regels
from mboek.models.auto_booking_rules import (
    AutoBookingRuleResponse,
    NewAutoBookingRule,
    UpdateAutoBookingRule,
)
from mboek.models.boekingen import BoekingMetRegelsResponse
from mboek.resources._base import BaseResource


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

    def list(self) -> list[AutoBookingRuleResponse]:
        """Return all automatic booking rules for the administratie.

        Returns:
            List sorted by priority ascending, then name.
        """
        return [
            parse_auto_booking_rule(d)
            for d in self._get(f"/api/administraties/{self._admin_id}/regels")
        ]

    def create(self, input: NewAutoBookingRule) -> AutoBookingRuleResponse:
        """Create a new automatic booking rule.

        Rule lines may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        IDs are resolved automatically.

        Args:
            input: Rule definition.
        """
        self._resolve_lines(input.lines)
        return parse_auto_booking_rule(
            self._post(
                f"/api/administraties/{self._admin_id}/regels", json=input.to_dict()
            )
        )

    def update(
        self, rule_id: int, input: UpdateAutoBookingRule
    ) -> AutoBookingRuleResponse:
        """Partially update a rule.

        Rule lines may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        IDs are resolved automatically.

        Args:
            rule_id: Rule ID.
            input: Fields to update.
        """
        if input.lines is not None:
            self._resolve_lines(input.lines)
        return parse_auto_booking_rule(
            self._patch(
                f"/api/administraties/{self._admin_id}/regels/{rule_id}",
                json=input.to_dict(),
            )
        )

    def _resolve_lines(self, lines: list) -> None:
        """Resolve grootboekrekening naam/code → id for each line in-place."""
        from mboek.models.auto_booking_rules import NewAutoBookingRuleLine

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

    def apply_to_boeking(self, boeking_id: int) -> BoekingMetRegelsResponse | None:
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
