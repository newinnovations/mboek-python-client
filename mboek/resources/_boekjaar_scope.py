"""BoekjaarScopedBoekingenResource — boekingen scoped to a dagboek + boekjaar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mboek.resources._base import BaseResource

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekingen import BoekingMetRegelsResponse, NewBoeking


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

    def list(self) -> list["BoekingMetRegelsResponse"]:
        """Return all boekingen for this dagboek within the fiscal year.

        Each boeking is returned together with all its boekingsregels.

        Returns:
            List ordered by date and ID ascending.
        """
        from mboek._parsers import parse_boeking_met_regels

        return [
            parse_boeking_met_regels(d)
            for d in self._client._request(
                "GET",
                f"/api/dagboeken/{self._dagboek_id}/boekingen",
                params={"boekjaar_id": self._boekjaar_id},
            )
        ]

    def create(self, input: "NewBoeking") -> "BoekingMetRegelsResponse":
        """Create a new boeking with its boekingsregels in a single transaction.

        The scope's ``boekjaar_id`` is always injected into the request,
        overriding any value set on ``input``. All regels must balance
        (``sum(bedrag) == 0``).

        Regels may reference a grootboekrekening via ``grootboekrekening_naam``
        or ``grootboekrekening_code`` instead of ``grootboekrekening_id``; the
        ID is resolved automatically (using the client-level cache).

        Args:
            input: :py:class:`~mboek.models.boekingen.NewBoeking` — boeking
                header and lines. The ``boekjaar_id`` field may be omitted; the
                scope provides it automatically.

        Returns:
            The newly created boeking with all its regels.

        Raises:
            :py:class:`~mboek._exceptions.ValidationError`: Regels do not balance
                or fewer than 2 regels provided.
            :py:class:`~mboek._exceptions.NotFoundError`: A naam/code could not
                be resolved to a grootboekrekening.
        """
        from mboek._parsers import parse_boeking_met_regels

        for regel in input.regels:
            if regel.grootboekrekening_id is None:
                regel.grootboekrekening_id = self._resolve_rekening_id(
                    self._admin_id,
                    naam=regel.grootboekrekening_naam,
                    code=regel.grootboekrekening_code,
                )

        data = input.to_dict()
        data["boekjaar_id"] = self._boekjaar_id

        return parse_boeking_met_regels(
            self._client._request(
                "POST",
                f"/api/dagboeken/{self._dagboek_id}/boekingen",
                json=data,
            )
        )
