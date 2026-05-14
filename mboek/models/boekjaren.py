"""Boekjaar (fiscal year) models."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from mboek.models._enums import BoekjaarStatus

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.dagboeken import Dagboek
    from mboek.models.grootboekrekeningen import Grootboekrekening
    from mboek.models.jaarrekening import JaarrekeningHtmlReport, JaarrekeningPdfReport
    from mboek.resources.btw_aangifte import BtwAangifteResource
    from mboek.resources.reports import ReportsResource


def _derive_bedrijf_from_administratie_naam(naam: str) -> str:
    without_bv = re.sub(r"\bbv\b", "", naam, flags=re.IGNORECASE)
    bedrijf = "".join(without_bv.lower().split())
    if not bedrijf:
        raise ValueError(
            "Could not derive bedrijf from administratie name; provide bedrijf explicitly"
        )
    return bedrijf


class Boekjaar:
    """A fiscal year belonging to an administratie.

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds a client reference that unlocks scope-specific operations
    such as :py:attr:`reports`, :py:attr:`btw_aangifte`,
    :py:meth:`dagboeken`, :py:meth:`dagboek`,
    :py:meth:`jaarrekening_html`, and :py:meth:`jaarrekening_pdf`.

    Obtain a fully-scoped instance via the admin scope helper::

        boekjaar = client.administratie(1).boekjaar(name="2024")
        boekjaar.reports.balans()
        boekjaar.dagboeken(code="BANK")[0].boekingen.list()
        boekjaar.dagboek(code="BANK").boekingen.list()
        boekjaar.jaarrekening_html()

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
        self._reports: ReportsResource | None = None
        self._btw_aangifte: BtwAangifteResource | None = None

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
    def reports(self) -> "ReportsResource":
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
    def btw_aangifte(self) -> "BtwAangifteResource":
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

    def grootboekrekeningen(
        self, *, limit: int | None = None, offset: int | None = None
    ) -> "list[Grootboekrekening]":
        """Return all grootboekrekeningen for this boekjaar, enriched with balance.

        Args:
            limit: Maximum number of rekeningen to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of rekeningen to skip before collecting results.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("grootboekrekeningen()")
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        return GrootboekrekeningenResource(client, self.administratie_id).met_saldo(
            self.id,
            limit=limit,
            offset=offset,
        )

    def grootboekrekening(self, *, code: int) -> "Grootboekrekening":
        """Return a single grootboekrekening for this boekjaar, looked up by account code.

        Args:
            code: Account code to search for (e.g. ``4000``).

        Raises:
            :py:class:`~mboek._exceptions.NotFoundError`: No account found.
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        from mboek._exceptions import NotFoundError

        found = next((r for r in self.grootboekrekeningen() if r.code == code), None)
        if found is None:
            raise NotFoundError(f"Grootboekrekening with code '{code}' not found")
        return found

    def dagboeken(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        code: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> "list[Dagboek]":
        """Return dagboeken for this boekjaar, each scoped to it.

        All filters are exact matches and are combined with ``AND`` semantics.
        The ``code`` filter is case-insensitive.

        Args:
            limit: Maximum number of dagboeken to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of dagboeken to skip before collecting results.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("dagboeken()")
        from mboek.resources.dagboeken import DagboekenResource

        return [
            dagboek.with_boekjaar(id=self.id)
            for dagboek in DagboekenResource(client, self.administratie_id).list(
                id=id,
                name=name,
                code=code,
                limit=limit,
                offset=offset,
            )
        ]

    def dagboek(
        self,
        id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
    ) -> "Dagboek":
        """Return a :py:class:`~mboek.models.dagboeken.Dagboek` scoped to this boekjaar.

        Pass the numeric ``id`` (one HTTP call to fetch data), a
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
        provided = sum(x is not None for x in [id, name, code])
        if provided != 1:
            raise ValueError("Provide exactly one of: id, name, code")
        from mboek.resources.dagboeken import DagboekenResource

        dagboeken = DagboekenResource(client, self.administratie_id)
        if id is not None:
            found = dagboeken.get(id).with_boekjaar(id=self.id)
        elif name is not None:
            found = dagboeken._require_single_match(
                self.dagboeken(name=name),
                not_found_message=f"Dagboek '{name}' not found",
                multiple_message=f"Multiple dagboeken named '{name}' found",
            )
        else:
            if code is None:
                raise AssertionError("dagboek() could not resolve dagboek filters")
            found = dagboeken._require_single_match(
                self.dagboeken(code=code),
                not_found_message=f"Dagboek with code '{code}' not found",
                multiple_message=f"Multiple dagboeken with code '{code}' found",
            )
        return found

    def _resolve_jaarrekening_shorthand(
        self,
        *,
        client: "MboekClient",
        config_path: str | None,
        bedrijf: str | None,
        jaar: int | None,
    ) -> tuple[str | None, str | None, int | None]:
        if config_path is not None:
            return config_path, bedrijf, jaar
        resolved_bedrijf = bedrijf
        if resolved_bedrijf is None:
            administratie = client.administraties.get(self.administratie_id)
            resolved_bedrijf = _derive_bedrijf_from_administratie_naam(administratie.naam)
        resolved_jaar = self.start_datum.year if jaar is None else jaar
        return None, resolved_bedrijf, resolved_jaar

    def jaarrekening_html(
        self,
        *,
        config_path: str | None = None,
        bedrijf: str | None = None,
        jaar: int | None = None,
        debug: bool = False,
        minimal: bool = False,
        consolidatie: bool = False,
        write_beginbalans: bool = False,
    ) -> "JaarrekeningHtmlReport":
        """Generate a jaarrekening HTML report for this boekjaar.

        When ``config_path`` is omitted, ``bedrijf`` defaults to the owning
        administratie name with ``BV`` removed, spaces stripped, and the result
        lowercased. ``jaar`` defaults to ``start_datum.year``.

        Returns:
            :py:class:`~mboek.models.jaarrekening.JaarrekeningHtmlReport`.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("jaarrekening_html()")
        config_path, bedrijf, jaar = self._resolve_jaarrekening_shorthand(
            client=client,
            config_path=config_path,
            bedrijf=bedrijf,
            jaar=jaar,
        )
        return client.jaarrekening.generate_html(
            config_path=config_path,
            bedrijf=bedrijf,
            jaar=jaar,
            debug=debug,
            minimal=minimal,
            consolidatie=consolidatie,
            write_beginbalans=write_beginbalans,
        )

    def jaarrekening_pdf(
        self,
        *,
        config_path: str | None = None,
        bedrijf: str | None = None,
        jaar: int | None = None,
        debug: bool = False,
        minimal: bool = False,
        consolidatie: bool = False,
        write_beginbalans: bool = False,
    ) -> "JaarrekeningPdfReport":
        """Generate a jaarrekening PDF report for this boekjaar.

        When ``config_path`` is omitted, ``bedrijf`` defaults to the owning
        administratie name with ``BV`` removed, spaces stripped, and the result
        lowercased. ``jaar`` defaults to ``start_datum.year``.

        Returns:
            :py:class:`~mboek.models.jaarrekening.JaarrekeningPdfReport`.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("jaarrekening_pdf()")
        config_path, bedrijf, jaar = self._resolve_jaarrekening_shorthand(
            client=client,
            config_path=config_path,
            bedrijf=bedrijf,
            jaar=jaar,
        )
        return client.jaarrekening.generate_pdf(
            config_path=config_path,
            bedrijf=bedrijf,
            jaar=jaar,
            debug=debug,
            minimal=minimal,
            consolidatie=consolidatie,
            write_beginbalans=write_beginbalans,
        )

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
