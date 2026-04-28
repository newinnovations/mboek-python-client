"""Boekingen resource."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from mboek._parsers import parse_boeking_met_regels
from mboek.models._enums import BoekingStatus
from mboek.models.boekingen import BoekingResponse
from mboek.resources._base import BaseResource

if TYPE_CHECKING:
    from mboek.models.boekingen import NewBoekingsregel


class BoekingenResource(BaseResource):
    """Operations on boekingen (journal entries) by ID.

    Access via :py:attr:`MboekClient.boekingen`.

    To **list** or **create** boekingen, use the boekjaar-scoped access::

        bj = client.administratie(1).boekjaar(10)
        entries = bj.dagboek(20).boekingen.list()

    .. note::
        The API has an asymmetry: boekingen are **listed and created** under
        ``/api/dagboeken/{dagboek_id}/boekingen`` but **retrieved, updated and
        deleted** at ``/api/boekingen/{id}``.
    """

    def get(self, id: int) -> BoekingResponse:
        """Return a single boeking with all its boekingsregels.

        Args:
            id: Boeking ID.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: Not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        return parse_boeking_met_regels(self._get(f"/api/boekingen/{id}"))

    def update(
        self,
        id: int,
        *,
        datum: date | None = None,
        omschrijving: str | None = None,
        stuknummer: str | None = None,
        status: BoekingStatus | None = None,
        tegenpartij_naam: str | None = None,
        tegenpartij_iban: str | None = None,
        gecontroleerd: bool | None = None,
        auto_geboekt: bool | None = None,
        regels: "list[NewBoekingsregel] | None" = None,
    ) -> BoekingResponse:
        """Update a boeking's header fields and optionally replace all regels.

        If ``regels`` is provided the existing regels are deleted and the new
        set is inserted atomically. Manually editing regels automatically
        clears the ``auto_geboekt`` and ``gecontroleerd`` flags.

        Args:
            id: Boeking ID.
            datum: New booking date.
            omschrijving: New description.
            stuknummer: New document reference.
            status: New status.
            tegenpartij_naam: New counterparty name.
            tegenpartij_iban: New counterparty IBAN.
            gecontroleerd: Mark as manually reviewed.
            auto_geboekt: Mark as auto-booked.
            regels: Full replacement set of lines (must balance).

        Returns:
            The updated boeking.
        """
        data: dict = {}
        if datum is not None:
            data["datum"] = datum.isoformat()
        if omschrijving is not None:
            data["omschrijving"] = omschrijving
        if stuknummer is not None:
            data["stuknummer"] = stuknummer
        if status is not None:
            data["status"] = status.value
        if tegenpartij_naam is not None:
            data["tegenpartij_naam"] = tegenpartij_naam
        if tegenpartij_iban is not None:
            data["tegenpartij_iban"] = tegenpartij_iban
        if gecontroleerd is not None:
            data["gecontroleerd"] = gecontroleerd
        if auto_geboekt is not None:
            data["auto_geboekt"] = auto_geboekt
        if regels is not None:
            data["regels"] = [r.to_dict() for r in regels]
        return parse_boeking_met_regels(self._patch(f"/api/boekingen/{id}", json=data))

    def delete(self, id: int) -> None:
        """Permanently delete a boeking and all its boekingsregels.

        Args:
            id: Boeking ID.
        """
        self._delete(f"/api/boekingen/{id}")
