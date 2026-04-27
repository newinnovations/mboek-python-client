"""Boekingen resource."""

from __future__ import annotations

from mboek._parsers import parse_boeking_met_regels
from mboek.models.boekingen import (
    BoekingMetRegelsResponse,
    UpdateBoekingInput,
)
from mboek.resources._base import BaseResource


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

    def get(self, id: int) -> BoekingMetRegelsResponse:
        """Return a single boeking with all its boekingsregels.

        Args:
            id: Boeking ID.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: Not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        return parse_boeking_met_regels(self._get(f"/api/boekingen/{id}"))

    def update(self, id: int, input: UpdateBoekingInput) -> BoekingMetRegelsResponse:
        """Update a boeking's header fields and optionally replace all regels.

        If ``regels`` is provided the existing regels are deleted and the new
        set is inserted atomically. Manually editing regels automatically
        clears the ``auto_geboekt`` and ``gecontroleerd`` flags.

        Args:
            id: Boeking ID.
            input: Fields to update (all optional).

        Returns:
            The updated boeking.
        """
        return parse_boeking_met_regels(
            self._patch(f"/api/boekingen/{id}", json=input.to_dict())
        )

    def delete(self, id: int) -> None:
        """Permanently delete a boeking and all its boekingsregels.

        Args:
            id: Boeking ID.
        """
        self._delete(f"/api/boekingen/{id}")
