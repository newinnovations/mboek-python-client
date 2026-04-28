"""Boekjaar (fiscal year) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from mboek.models._enums import BoekjaarStatus

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.dagboeken import Dagboek
    from mboek.models.grootboekrekeningen import (
        Grootboekrekening,
        GrootboekrekeningMetSaldoResponse,
    )


class Boekjaar:
    """A fiscal year belonging to an administratie.

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds a client reference that unlocks scope-specific operations
    such as :py:attr:`reports`, :py:attr:`btw_aangifte`, and
    :py:meth:`dagboek`.

    Obtain a fully-scoped instance via the admin scope helper::

        boekjaar = client.administratie(1).boekjaar(name="2024")
        boekjaar.reports.balans()
        boekjaar.dagboek(code="BANK").boekingen.list()

    A ``Boekjaar`` obtained from :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.list`
    carries a client reference automatically, so scope-specific methods work
    directly on those objects too::

        for bj in client.administratie(1).boekjaren.list():
            print(bj.naam, bj.reports.balans())

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        naam: Display name (e.g. ``"2024"``).
        start_datum: First day of the fiscal year.
        eind_datum: Last day of the fiscal year.
        status: ``open`` (accepting new boekingen) or ``gesloten`` (locked).
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    def __init__(
        self,
        id: int,
        administratie_id: int,
        naam: str,
        start_datum: date,
        eind_datum: date,
        status: BoekjaarStatus,
        created_at: datetime,
        updated_at: datetime,
        *,
        client: "MboekClient | None" = None,
    ) -> None:
        self.id = id
        self.administratie_id = administratie_id
        self.naam = naam
        self.start_datum = start_datum
        self.eind_datum = eind_datum
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self._client = client

        # Lazily-initialised child resources
        self._reports = None
        self._btw_aangifte = None

    # ── Internal scope guard ─────────────────────────────────────────────────

    def _require_client(self, operation: str) -> "MboekClient":
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError(
                f"{operation} requires a client reference. "
                "Obtain the boekjaar via client.administratie(...).boekjaar(...) "
                "or via client.administratie(...).boekjaren.list()."
            )
        return self._client

    # ── Scoped resource properties ────────────────────────────────────────────

    @property
    def reports(self):
        """Reports resource (:py:class:`~mboek.resources.reports.ReportsResource`).

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("reports")
        if self._reports is None:
            from mboek.resources.reports import ReportsResource

            self._reports = ReportsResource(client, self.administratie_id, self.id)
        return self._reports

    @property
    def btw_aangifte(self):
        """BTW-aangifte resource (:py:class:`~mboek.resources.btw_aangifte.BtwAangifteResource`).

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("btw_aangifte")
        if self._btw_aangifte is None:
            from mboek.resources.btw_aangifte import BtwAangifteResource

            self._btw_aangifte = BtwAangifteResource(
                client, self.administratie_id, self.id
            )
        return self._btw_aangifte

    # ── Scoped methods ────────────────────────────────────────────────────────

    def grootboekrekeningen(self) -> "list[GrootboekrekeningMetSaldoResponse]":
        """Return all grootboekrekeningen for this boekjaar, enriched with balance.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("grootboekrekeningen()")
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        return GrootboekrekeningenResource(client, self.administratie_id).met_saldo(
            self.id
        )

    def grootboekrekening(self, *, code: str) -> "Grootboekrekening":
        """Return a single grootboekrekening for this boekjaar, looked up by account code.

        Args:
            code: Account code to search for (e.g. ``"4000"``).

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: No account found.
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        from mboek._exceptions import NotFoundError

        found = next((r for r in self.grootboekrekeningen() if r.code == code), None)
        if found is None:
            raise NotFoundError(f"Grootboekrekening with code '{code}' not found")
        return found

    def dagboek(
        self,
        dagboek_id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
    ) -> "Dagboek":
        """Return a :py:class:`~mboek.models.dagboeken.Dagboek` scoped to this boekjaar.

        Pass the numeric ``dagboek_id`` (one HTTP call to fetch data), a
        ``name``, or a ``code`` to look up by exact name or short code::

            dagboek = boekjaar.dagboek(20)
            dagboek = boekjaar.dagboek(name="Bankboek")
            dagboek = boekjaar.dagboek(code="BANK")

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` or ``code``
                given but no matching dagboek found.
            :py:exc:`ValueError`: None or more than one argument provided.
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("dagboek()")
        provided = sum(x is not None for x in [dagboek_id, name, code])
        if provided != 1:
            raise ValueError("Provide exactly one of: dagboek_id, name, code")
        from mboek.resources.dagboeken import DagboekenResource

        dagboeken = DagboekenResource(client, self.administratie_id)
        if dagboek_id is not None:
            found = dagboeken.get(dagboek_id)
        elif name is not None:
            from mboek._exceptions import NotFoundError

            found = dagboeken.find_by_naam(name)
            if found is None:
                raise NotFoundError(f"Dagboek '{name}' not found")
        else:
            from mboek._exceptions import NotFoundError

            found = dagboeken.find_by_code(code)  # type: ignore[arg-type]
            if found is None:
                raise NotFoundError(f"Dagboek with code '{code}' not found")
        return found.with_boekjaar(boekjaar_id=self.id)

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Boekjaar(id={self.id!r}, naam={self.naam!r},"
            f" administratie_id={self.administratie_id!r}, status={self.status!r})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Boekjaar):
            return NotImplemented
        return self.id == other.id and self.administratie_id == other.administratie_id


# Keep a type alias consistent with response naming used in other modules.
BoekjaarResponse = Boekjaar


@dataclass
class NewBoekjaar:
    """Input for creating a new boekjaar.

    Attributes:
        naam: Display name (e.g. ``"2024"``).
        start_datum: First day of the fiscal year (``YYYY-MM-DD``).
        eind_datum: Last day of the fiscal year (``YYYY-MM-DD``).
    """

    naam: str
    start_datum: date
    eind_datum: date

    def to_dict(self) -> dict:
        return {
            "naam": self.naam,
            "start_datum": self.start_datum.isoformat(),
            "eind_datum": self.eind_datum.isoformat(),
        }


@dataclass
class UpdateBoekjaar:
    """Input for partially updating a boekjaar.

    All fields optional. Do **not** use this to close/reopen a boekjaar —
    use the dedicated :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.afsluiten`
    and :py:meth:`~mboek.resources.boekjaren.BoekjarenResource.heropenen` methods.

    Attributes:
        naam: New display name.
        start_datum: New start date.
        eind_datum: New end date.
    """

    naam: str | None = None
    start_datum: date | None = None
    eind_datum: date | None = None

    def to_dict(self) -> dict:
        d: dict = {}
        if self.naam is not None:
            d["naam"] = self.naam
        if self.start_datum is not None:
            d["start_datum"] = self.start_datum.isoformat()
        if self.eind_datum is not None:
            d["eind_datum"] = self.eind_datum.isoformat()
        return d
