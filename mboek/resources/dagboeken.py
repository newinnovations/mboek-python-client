"""Dagboeken resource."""

from __future__ import annotations

import builtins

from mboek._parsers import parse_dagboek, parse_werkstatus
from mboek._unset import UNSET, UnsetType
from mboek.models._enums import DagboekType
from mboek.models.dagboeken import Dagboek, DagboekWerkStatus
from mboek.resources._base import BaseResource


class DagboekenResource(BaseResource):
    """CRUD + werkstatus operations for dagboeken (journals / sub-ledgers).

    Instantiated via :py:meth:`AdministratieScope.dagboeken`.

    Dagboek types:

    - ``bank`` — bank account (linked to a balance-sheet rekening + optional IBAN)
    - ``kas`` — cash book
    - ``inkoop`` — purchase journal
    - ``verkoop`` — sales journal
    - ``memoriaal`` — general journal (full double-entry)
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        code: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[Dagboek]:
        """Return dagboeken for the administratie.

        All filters are exact matches and are combined with ``AND`` semantics.
        The ``code`` filter is case-insensitive.
        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically before client-side filtering is applied.

        Returns:
            List sorted by code ascending.
        """
        filtered = id is not None or name is not None or code is not None
        items = [
            parse_dagboek(d, client=self._client)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/dagboeken",
                limit=None if filtered else limit,
                offset=None if filtered else offset,
            )
        ]
        if id is not None:
            items = [item for item in items if item.id == id]
        if name is not None:
            items = [item for item in items if item.naam == name]
        if code is not None:
            code_upper = code.upper()
            items = [item for item in items if item.code.upper() == code_upper]
        if filtered:
            return self._slice_items(items, limit=limit, offset=offset)
        return items

    def get(self, id: int) -> Dagboek:
        """Return a single dagboek.

        Args:
            id: Dagboek ID.
        """
        return parse_dagboek(
            self._get(f"/api/administraties/{self._admin_id}/dagboeken/{id}"),
            client=self._client,
        )

    def create(
        self,
        code: str,
        naam: str,
        dagboek_type: DagboekType,
        *,
        grootboekrekening_id: int | None = None,
        grootboekrekening_naam: str | None = None,
        grootboekrekening_code: str | None = None,
        iban: str | None = None,
    ) -> Dagboek:
        """Create a new dagboek.

        At most one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
        ``grootboekrekening_code`` may be provided.  When a name or code is supplied
        the ID is resolved automatically.

        Args:
            code: Short code (e.g. ``"BANK"``).
            naam: Display name.
            dagboek_type: Journal type.
            grootboekrekening_id: Optional linked balance account (numeric ID).
            grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
            grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
            iban: Optional IBAN for bank-statement auto-matching.
        """
        provided = sum(
            x is not None
            for x in [
                grootboekrekening_id,
                grootboekrekening_naam,
                grootboekrekening_code,
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )
        grootboekrekening_id = self._resolve_rekening_reference(
            self._admin_id,
            id_value=grootboekrekening_id,
            name_value=grootboekrekening_naam,
            code_value=grootboekrekening_code,
        )
        data: dict = {
            "code": code,
            "naam": naam,
            "dagboek_type": dagboek_type.value,
        }
        if grootboekrekening_id is not None:
            data["grootboekrekening_id"] = grootboekrekening_id
        if iban is not None:
            data["iban"] = iban
        return parse_dagboek(
            self._post(f"/api/administraties/{self._admin_id}/dagboeken", json=data),
            client=self._client,
        )

    def update(
        self,
        id: int,
        *,
        code: str | None | UnsetType = UNSET,
        naam: str | None | UnsetType = UNSET,
        dagboek_type: DagboekType | None | UnsetType = UNSET,
        grootboekrekening_id: int | None | UnsetType = UNSET,
        grootboekrekening_naam: str | None | UnsetType = UNSET,
        grootboekrekening_code: str | None | UnsetType = UNSET,
        iban: str | None | UnsetType = UNSET,
    ) -> Dagboek:
        """Partially update a dagboek.

        At most one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
        ``grootboekrekening_code`` may be provided.  When a name or code is supplied
        the ID is resolved automatically.
        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

        Args:
            id: Dagboek ID.
            code: New short code.
            naam: New display name.
            dagboek_type: New journal type.
            grootboekrekening_id: New linked balance account (numeric ID).
            grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
            grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
            iban: New IBAN.
        """
        provided = sum(
            x is not UNSET
            for x in [
                grootboekrekening_id,
                (
                    grootboekrekening_naam
                    if grootboekrekening_naam is not None
                    else UNSET
                ),
                (
                    grootboekrekening_code
                    if grootboekrekening_code is not None
                    else UNSET
                ),
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )
        grootboekrekening_id = self._resolve_rekening_reference_patch(
            self._admin_id,
            id_value=grootboekrekening_id,
            name_value=grootboekrekening_naam,
            code_value=grootboekrekening_code,
        )
        data: dict = {}
        self._set_patch_value(data, "code", code)
        self._set_patch_value(data, "naam", naam)
        self._set_patch_enum(data, "dagboek_type", dagboek_type)
        self._set_patch_value(data, "grootboekrekening_id", grootboekrekening_id)
        self._set_patch_value(data, "iban", iban)
        return parse_dagboek(
            self._patch(
                f"/api/administraties/{self._admin_id}/dagboeken/{id}", json=data
            ),
            client=self._client,
        )

    def delete(self, id: int) -> None:
        """Permanently delete a dagboek.

        Fails if the dagboek has existing boekingen.

        Args:
            id: Dagboek ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/dagboeken/{id}")

    def werkstatus(
        self,
        boekjaar_id: int | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list[DagboekWerkStatus]:
        """Return per-dagboek work-status counts.

        Returns the number of unprocessed bank imports (``onverwerkt``) and
        unconfirmed auto-booked entries (``te_bevestigen``) for each dagboek.

        Args:
            boekjaar_id: Fiscal year to query. Defaults to the administratie's
                ``huidig_boekjaar_id`` when omitted.
            limit: Maximum number of dagboeken to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of dagboeken to skip before collecting results.

        Returns:
            One :py:class:`~mboek.models.dagboeken.DagboekWerkStatus` per
            dagboek that has non-zero counts.
        """
        return [
            parse_werkstatus(d)
            for d in self._get_paginated(
                f"/api/administraties/{self._admin_id}/dagboeken/werkstatus",
                params={"boekjaar_id": boekjaar_id},
                limit=limit,
                offset=offset,
            )
        ]
