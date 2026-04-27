"""BoekjaarScope — scoped access to boekjaar-level resources and operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mboek._exceptions import NotFoundError

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekingen import BoekingMetRegelsResponse, CreateBoekingInput


class BoekjaarScopedBoekingenResource:
    """Boekingen operations scoped to a single dagboek within a boekjaar.

    Handles ``list`` and ``create``. Use :py:attr:`MboekClient.boekingen` for
    ``get``, ``update`` and ``delete`` (which operate by boeking ID only).
    """

    def __init__(self, client: "MboekClient", boekjaar_id: int, dagboek_id: int) -> None:
        self._client = client
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

    def create(self, input: "CreateBoekingInput") -> "BoekingMetRegelsResponse":
        """Create a new boeking with its boekingsregels in a single transaction.

        The scope's ``boekjaar_id`` is always injected into the request,
        overriding any value set on ``input``. All regels must balance
        (``sum(bedrag) == 0``).

        Args:
            input: :py:class:`~mboek.models.boekingen.CreateBoekingInput` — boeking
                header and lines. The ``boekjaar_id`` field may be omitted; the
                scope provides it automatically.

        Returns:
            The newly created boeking with all its regels.

        Raises:
            :py:class:`~mboek._exceptions.ValidationError`: Regels do not balance
                or fewer than 2 regels provided.
        """
        from mboek._parsers import parse_boeking_met_regels

        data = input.to_dict()
        data["boekjaar_id"] = self._boekjaar_id

        return parse_boeking_met_regels(
            self._client._request(
                "POST",
                f"/api/dagboeken/{self._dagboek_id}/boekingen",
                json=data,
            )
        )


class BoekjaarDagboekScope:
    """Scoped access to boekingen within a specific dagboek and boekjaar.

    Obtain via :py:meth:`~mboek.resources._boekjaar_scope.BoekjaarScope.dagboek`::

        scope = client.administratie(1).boekjaar(10).dagboek(20)
        entries = scope.boekingen.list()
        scope.boekingen.create(inp)

    No HTTP call is made when creating this object.
    """

    def __init__(
        self, client: "MboekClient", admin_id: int, boekjaar_id: int, dagboek_id: int
    ) -> None:
        self._client = client
        self._admin_id = admin_id
        self._boekjaar_id = boekjaar_id
        self._dagboek_id = dagboek_id

        self._boekingen: BoekjaarScopedBoekingenResource | None = None

    @property
    def boekingen(self) -> BoekjaarScopedBoekingenResource:
        """Scoped boekingen resource for this dagboek and boekjaar."""
        if self._boekingen is None:
            self._boekingen = BoekjaarScopedBoekingenResource(
                self._client, self._boekjaar_id, self._dagboek_id
            )
        return self._boekingen


class BoekjaarScope:
    """Scoped access to all boekjaar-level resources.

    Obtain via :py:meth:`~mboek.resources._admin_scope.AdministratieScope.boekjaar`::

        bj = client.administratie(1).boekjaar(10)
        bj.reports.balans()
        bj.btw_aangifte.list()
        bj.dagboek(20).boekingen.list()

    No HTTP call is made when creating this object.
    """

    def __init__(self, client: "MboekClient", admin_id: int, boekjaar_id: int) -> None:
        self._client = client
        self._admin_id = admin_id
        self.boekjaar_id = boekjaar_id

        self._reports = None
        self._btw_aangifte = None

    @property
    def reports(self):
        """Reports resource (:py:class:`~mboek.resources.reports.ReportsResource`)."""
        if self._reports is None:
            from mboek.resources.reports import ReportsResource

            self._reports = ReportsResource(self._client, self._admin_id, self.boekjaar_id)
        return self._reports

    @property
    def btw_aangifte(self):
        """BTW-aangifte resource (:py:class:`~mboek.resources.btw_aangifte.BtwAangifteResource`)."""
        if self._btw_aangifte is None:
            from mboek.resources.btw_aangifte import BtwAangifteResource

            self._btw_aangifte = BtwAangifteResource(
                self._client, self._admin_id, self.boekjaar_id
            )
        return self._btw_aangifte

    def dagboek(
        self,
        dagboek_id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
    ) -> BoekjaarDagboekScope:
        """Return a :py:class:`BoekjaarDagboekScope`.

        Pass the numeric ``dagboek_id`` (no HTTP call), a ``name``, or a
        ``code`` to look up by exact name or short code (one HTTP call each)::

            scope = bj.dagboek(20)
            scope = bj.dagboek(name="Bankboek")
            scope = bj.dagboek(code="BANK")

        Args:
            dagboek_id: Dagboek ID. No HTTP call is made.
            name: Exact dagboek name (case-sensitive). Performs a
                :py:meth:`~mboek.resources.dagboeken.DagboekenResource.list`
                lookup request.
            code: Dagboek short code (case-insensitive). Performs a
                :py:meth:`~mboek.resources.dagboeken.DagboekenResource.list`
                lookup request.

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` or ``code``
                given but no matching dagboek found.
            :py:exc:`ValueError`: None or more than one of the arguments
                provided.
        """
        provided = sum(x is not None for x in [dagboek_id, name, code])
        if provided != 1:
            raise ValueError("Provide exactly one of: dagboek_id, name, code")
        if name is not None or code is not None:
            from mboek.resources.dagboeken import DagboekenResource

            dagboeken = DagboekenResource(self._client, self._admin_id)
            if name is not None:
                found = dagboeken.find_by_naam(name)
                label = f"'{name}'"
            else:
                found = dagboeken.find_by_code(code)
                label = f"with code '{code}'"
            if found is None:
                raise NotFoundError(f"Dagboek {label} not found")
            dagboek_id = found.id
        return BoekjaarDagboekScope(
            self._client, self._admin_id, self.boekjaar_id, dagboek_id
        )
