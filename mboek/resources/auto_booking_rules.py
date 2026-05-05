"""Automatic booking rules resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from mboek._exceptions import MboekError
from mboek._parsers import parse_auto_booking_rule
from mboek._unset import UNSET, UnsetType
from mboek.models._enums import AutoBookingActieType
from mboek.models.auto_booking_rules import (
    AutoBookingRule,
    AutoBookingRuleApplicationResult,
)
from mboek.resources._base import BaseResource

if TYPE_CHECKING:
    from mboek.models.auto_booking_rules import NewAutoBookingRuleLine


class AutoBookingRulesResource(BaseResource):
    """CRUD + execution operations for automatic booking rules.

    Instantiated via :py:meth:`AdministratieScope.auto_booking_rules`.

    Rules are evaluated in ascending priority order; the first match wins.
    Each rule matches on:

    - ``iban_eigen`` — regex on the dagboek's own IBAN
    - ``iban_tegenpartij`` — regex on the counterparty IBAN
    - ``omschrijving_regex`` — regex on the transaction description

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
        lines: "builtins.list[NewAutoBookingRuleLine] | None" = None,
        *,
        prioriteit: int = 100,
        actief: bool = True,
        iban_eigen: str | None = None,
        iban_tegenpartij: str | None = None,
        omschrijving_regex: str | None = None,
        tegenrekening_id: int | None = None,
        tegenrekening_naam: str | None = None,
        tegenrekening_code: str | None = None,
        btw_code_id: int | None = None,
    ) -> AutoBookingRule:
        """Create a new automatic booking rule.

        Rule lines may reference a tegenrekening via ``tegenrekening_naam``
        or ``tegenrekening_code`` instead of ``tegenrekening_id``; the
        IDs are resolved automatically.

        Args:
            naam: Human-readable name.
            actie_type: Action type (``enkel`` or ``splits``).
            lines: Optional action lines.
            prioriteit: Sort priority (lower = evaluated first, default 100).
            actief: Enable the rule (default ``True``).
            iban_eigen: Regex for own IBAN matching.
            iban_tegenpartij: Regex for counterparty IBAN matching.
            omschrijving_regex: Regex for transaction description matching.
        """
        tegenrekening_id = self._resolve_rekening_reference(
            self._admin_id,
            id_value=tegenrekening_id,
            name_value=tegenrekening_naam,
            code_value=tegenrekening_code,
            field_prefix="tegenrekening",
        )
        data: dict = {
            "naam": naam,
            "actie_type": actie_type.value,
            "prioriteit": prioriteit,
            "actief": actief,
        }
        if lines is not None:
            data["lines"] = self._serialize_auto_booking_rule_lines(
                self._admin_id, lines
            )
        if iban_eigen is not None:
            data["iban_eigen"] = iban_eigen
        if iban_tegenpartij is not None:
            data["iban_tegenpartij"] = iban_tegenpartij
        if omschrijving_regex is not None:
            data["omschrijving_regex"] = omschrijving_regex
        if tegenrekening_id is not None:
            data["tegenrekening_id"] = tegenrekening_id
        if btw_code_id is not None:
            data["btw_code_id"] = btw_code_id
        return parse_auto_booking_rule(
            self._post(f"/api/administraties/{self._admin_id}/regels", json=data)
        )

    def update(
        self,
        rule_id: int,
        *,
        naam: str | None | UnsetType = UNSET,
        prioriteit: int | None | UnsetType = UNSET,
        actief: bool | None | UnsetType = UNSET,
        actie_type: AutoBookingActieType | None | UnsetType = UNSET,
        iban_eigen: str | None | UnsetType = UNSET,
        iban_tegenpartij: str | None | UnsetType = UNSET,
        omschrijving_regex: str | None | UnsetType = UNSET,
        tegenrekening_id: int | None | UnsetType = UNSET,
        tegenrekening_naam: str | None | UnsetType = UNSET,
        tegenrekening_code: str | None | UnsetType = UNSET,
        btw_code_id: int | None | UnsetType = UNSET,
        lines: "builtins.list[NewAutoBookingRuleLine] | None | UnsetType" = UNSET,
    ) -> AutoBookingRule:
        """Partially update a rule.

        Rule lines may reference a tegenrekening via ``tegenrekening_naam``
        or ``tegenrekening_code`` instead of ``tegenrekening_id``; the
        IDs are resolved automatically.
        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

        Args:
            rule_id: Rule ID.
            naam: New name.
            prioriteit: New sort priority.
            actief: Enable or disable the rule.
            actie_type: New action type.
            iban_eigen: New regex for own IBAN matching.
            iban_tegenpartij: New regex for counterparty IBAN matching.
            omschrijving_regex: New regex for description matching.
            lines: Full replacement set of action lines.
        """
        tegenrekening_id = self._resolve_rekening_reference_patch(
            self._admin_id,
            id_value=tegenrekening_id,
            name_value=tegenrekening_naam,
            code_value=tegenrekening_code,
            field_prefix="tegenrekening",
        )
        data: dict = {}
        self._set_patch_value(data, "naam", naam)
        self._set_patch_value(data, "prioriteit", prioriteit)
        self._set_patch_value(data, "actief", actief)
        self._set_patch_enum(data, "actie_type", actie_type)
        self._set_patch_value(data, "iban_eigen", iban_eigen)
        self._set_patch_value(data, "iban_tegenpartij", iban_tegenpartij)
        self._set_patch_value(data, "omschrijving_regex", omschrijving_regex)
        self._set_patch_value(data, "tegenrekening_id", tegenrekening_id)
        self._set_patch_value(data, "btw_code_id", btw_code_id)
        if not isinstance(lines, UnsetType):
            if lines is None:
                data["lines"] = None
            else:
                data["lines"] = self._serialize_auto_booking_rule_lines(
                    self._admin_id, lines
                )
        return parse_auto_booking_rule(
            self._patch(
                f"/api/administraties/{self._admin_id}/regels/{rule_id}", json=data
            )
        )

    def delete(self, rule_id: int) -> None:
        """Permanently delete a rule.

        Args:
            rule_id: Rule ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/regels/{rule_id}")

    def apply_to_boeking(self, boeking_id: int) -> AutoBookingRuleApplicationResult:
        """Apply the first matching rule to a single boeking.

        Args:
            boeking_id: Boeking ID.

        Returns:
            Structured result with the backend ``matched`` flag and optional
            diagnostic ``reason``.
        """
        data = self._post(
            f"/api/administraties/{self._admin_id}/boekingen/{boeking_id}/apply-rules"
        )
        if not isinstance(data, dict):
            raise MboekError(
                "apply_to_boeking() expected a JSON object response",
                detail=data,
            )
        matched = data.get("matched")
        if not isinstance(matched, bool):
            raise MboekError(
                "apply_to_boeking() expected a boolean 'matched' field",
                detail=data,
            )
        reason = data.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise MboekError(
                "apply_to_boeking() expected 'reason' to be a string or null",
                detail=data,
            )
        return AutoBookingRuleApplicationResult(matched=matched, reason=reason)
