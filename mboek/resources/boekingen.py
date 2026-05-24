"""Boekingen resource."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from mboek._parsers import parse_boeking_met_regels
from mboek._unset import UNSET, UnsetType
from mboek.models._enums import BoekingStatus
from mboek.models.boekingen import Boeking
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

    def get(self, id: int) -> Boeking:
        """Return a single boeking with all its boekingsregels.

        Args:
            id: Boeking ID.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: Not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        return parse_boeking_met_regels(
            self._get(f"/api/boekingen/{id}"), client=self._client
        )

    def update(
        self,
        id: int,
        *,
        admin_id: int | None = None,
        datum: date | None | UnsetType = UNSET,
        omschrijving: str | None | UnsetType = UNSET,
        stuknummer: str | None | UnsetType = UNSET,
        status: BoekingStatus | None | UnsetType = UNSET,
        tegenpartij_naam: str | None | UnsetType = UNSET,
        tegenpartij_iban: str | None | UnsetType = UNSET,
        gecontroleerd: bool | None | UnsetType = UNSET,
        auto_geboekt: bool | None | UnsetType = UNSET,
        regels: "list[NewBoekingsregel] | None | UnsetType" = UNSET,
    ) -> Boeking:
        """Update a boeking's header fields and optionally replace all regels.

        If ``regels`` is provided the existing regels are deleted and the new
        set is inserted atomically. Manually editing regels automatically
        clears the ``auto_geboekt`` and ``gecontroleerd`` flags.
        Regels may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        ID is resolved automatically.
        Pass ``None`` explicitly to clear a nullable field; omit a keyword to
        leave it unchanged.

        Args:
            id: Boeking ID.
            admin_id: Owning administratie ID. Provide this when replacing
                ``regels`` to skip the ownership lookup and keep the returned
                boeking scoped to the owning administratie.
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
        return self._update(
            id,
            admin_id=admin_id,
            datum=datum,
            omschrijving=omschrijving,
            stuknummer=stuknummer,
            status=status,
            tegenpartij_naam=tegenpartij_naam,
            tegenpartij_iban=tegenpartij_iban,
            gecontroleerd=gecontroleerd,
            auto_geboekt=auto_geboekt,
            regels=regels,
        )

    def _update(
        self,
        id: int,
        *,
        admin_id: int | None = None,
        datum: date | None | UnsetType = UNSET,
        omschrijving: str | None | UnsetType = UNSET,
        stuknummer: str | None | UnsetType = UNSET,
        status: BoekingStatus | None | UnsetType = UNSET,
        tegenpartij_naam: str | None | UnsetType = UNSET,
        tegenpartij_iban: str | None | UnsetType = UNSET,
        gecontroleerd: bool | None | UnsetType = UNSET,
        auto_geboekt: bool | None | UnsetType = UNSET,
        regels: "list[NewBoekingsregel] | None | UnsetType" = UNSET,
    ) -> Boeking:
        data: dict = {}
        self._set_patch_date(data, "datum", datum)
        self._set_patch_value(data, "omschrijving", omschrijving)
        self._set_patch_value(data, "stuknummer", stuknummer)
        self._set_patch_enum(data, "status", status)
        self._set_patch_value(data, "tegenpartij_naam", tegenpartij_naam)
        self._set_patch_value(data, "tegenpartij_iban", tegenpartij_iban)
        self._set_patch_value(data, "gecontroleerd", gecontroleerd)
        self._set_patch_value(data, "auto_geboekt", auto_geboekt)
        resolved_admin_id = admin_id
        if not isinstance(regels, UnsetType):
            if regels is None:
                data["regels"] = None
            else:
                admin_id_for_regels = resolved_admin_id
                if admin_id_for_regels is None:
                    admin_id_for_regels = self._resolve_admin_id_for_boeking(
                        boeking_id=id, admin_id=admin_id
                    )
                    resolved_admin_id = admin_id_for_regels
                if any(regel.grootboekrekening_id is None for regel in regels):
                    data["regels"] = self._serialize_boekingsregels(
                        admin_id_for_regels, regels
                    )
                else:
                    data["regels"] = [r.to_dict() for r in regels]
        return parse_boeking_met_regels(
            self._patch(f"/api/boekingen/{id}", json=data),
            client=self._client,
            administratie_id=resolved_admin_id,
        )

    def _resolve_admin_id_for_boeking(
        self, *, boeking_id: int, admin_id: int | None = None
    ) -> int:
        if admin_id is not None:
            return admin_id

        boeking = self.get(boeking_id)
        if boeking._administratie_id is not None:
            return boeking._administratie_id

        from mboek._exceptions import NotFoundError
        from mboek.resources.dagboeken import DagboekenResource

        cached_admin_id = self._client._dagboek_admin_cache.get(boeking.dagboek_id)
        if cached_admin_id is not None:
            return cached_admin_id

        for administratie in self._client.administraties.list():
            try:
                DagboekenResource(self._client, administratie.id).get(
                    boeking.dagboek_id
                )
            except NotFoundError:
                continue
            self._client._dagboek_admin_cache[boeking.dagboek_id] = administratie.id
            return administratie.id

        raise NotFoundError(
            f"Dagboek {boeking.dagboek_id} not found in any administratie"
        )

    def delete(self, id: int) -> None:
        """Permanently delete a boeking and all its boekingsregels.

        Args:
            id: Boeking ID.
        """
        self._delete(f"/api/boekingen/{id}")
