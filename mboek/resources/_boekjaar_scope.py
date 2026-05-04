"""BoekjaarScopedBoekingenResource — boekingen scoped to a dagboek + boekjaar."""

from __future__ import annotations

import builtins
from datetime import date
from typing import TYPE_CHECKING

from mboek.resources._base import BaseResource

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekingen import Boeking, NewBoekingsregel


class BoekjaarScopedBoekingenResource(BaseResource):
    """Boekingen operations scoped to a single dagboek within a boekjaar.

    Handles ``list`` and ``create``. Use :py:attr:`MboekClient.boekingen` for
    ``get``, ``update`` and ``delete`` (which operate by boeking ID only).

    Obtain via :py:attr:`~mboek.models.dagboeken.Dagboek.boekingen` on a
    boekjaar-scoped :py:class:`~mboek.models.dagboeken.Dagboek`::

        dagboek = client.administratie(1).boekjaar(10).dagboek(code="BANK")
        entries = dagboek.boekingen.list()
    """

    def __init__(
        self, client: "MboekClient", admin_id: int, boekjaar_id: int, dagboek_id: int
    ) -> None:
        super().__init__(client)
        self._admin_id = admin_id
        self._boekjaar_id = boekjaar_id
        self._dagboek_id = dagboek_id

    def list(
        self,
        *,
        id: int | None = None,
        item: str | int | None = None,
        description: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> builtins.list["Boeking"]:
        """Return boekingen for this dagboek within the fiscal year.

        All filters are exact matches and are combined with ``AND`` semantics.
        ``item`` matches ``stuknummer``.
        When ``limit`` and ``offset`` are omitted, all backend pages are fetched
        automatically before client-side filtering is applied.

        Each boeking is returned together with all its boekingsregels.

        Returns:
            List ordered by date and ID ascending.
        """
        from mboek._parsers import parse_boeking_met_regels

        filtered = id is not None or item is not None or description is not None
        items = [
            parse_boeking_met_regels(
                d,
                client=self._client,
                administratie_id=self._admin_id,
            )
            for d in self._get_paginated(
                f"/api/dagboeken/{self._dagboek_id}/boekingen",
                params={"boekjaar_id": self._boekjaar_id},
                limit=None if filtered else limit,
                offset=None if filtered else offset,
            )
        ]
        if id is not None:
            items = [entry for entry in items if entry.id == id]
        if item is not None:
            item_value = str(item)
            items = [entry for entry in items if entry.stuknummer == item_value]
        if description is not None:
            items = [entry for entry in items if entry.omschrijving == description]
        if filtered:
            return self._slice_items(items, limit=limit, offset=offset)
        return items

    def create(
        self,
        regels: "builtins.list[NewBoekingsregel]",
        datum: date,
        omschrijving: str,
        *,
        stuknummer: str | None = None,
        tegenpartij_naam: str | None = None,
        tegenpartij_iban: str | None = None,
        referentie_import: str | None = None,
        auto_geboekt: bool | None = None,
    ) -> "Boeking":
        """Create a new boeking with its boekingsregels in a single transaction.

        The scope's ``boekjaar_id`` is always injected into the request.
        All regels must balance (``sum(bedrag) == 0``).

        Regels may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        ID is resolved automatically (using the client-level cache).

        Args:
            regels: At least two balanced lines (``sum(bedrag) == 0``).
            datum: Booking date.
            omschrijving: Description.
            stuknummer: Optional document/invoice reference.
            tegenpartij_naam: Optional counterparty name.
            tegenpartij_iban: Optional counterparty IBAN.
            referentie_import: Optional external reference string.
            auto_geboekt: Set ``True`` to flag as system-generated.

        Returns:
            The newly created boeking with all its regels.

        Raises:
            :py:class:`~mboek._exceptions.ValidationError`: Regels do not balance
                or fewer than 2 regels provided.
            :py:class:`~mboek._exceptions.NotFoundError`: A naam/code could not
                be resolved to a grootboekrekening.
        """
        from mboek._parsers import parse_boeking_met_regels

        data: dict = {
            "boekjaar_id": self._boekjaar_id,
            "datum": datum.isoformat(),
            "omschrijving": omschrijving,
            "regels": self._serialize_boekingsregels(self._admin_id, regels),
        }
        if stuknummer is not None:
            data["stuknummer"] = stuknummer
        if tegenpartij_naam is not None:
            data["tegenpartij_naam"] = tegenpartij_naam
        if tegenpartij_iban is not None:
            data["tegenpartij_iban"] = tegenpartij_iban
        if referentie_import is not None:
            data["referentie_import"] = referentie_import
        if auto_geboekt is not None:
            data["auto_geboekt"] = auto_geboekt

        return parse_boeking_met_regels(
            self._client._request(
                "POST",
                f"/api/dagboeken/{self._dagboek_id}/boekingen",
                json=data,
            ),
            client=self._client,
            administratie_id=self._admin_id,
        )
