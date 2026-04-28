"""Dagboek (journal / sub-ledger) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mboek.models._enums import DagboekType

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.boekingen import BoekingMetRegelsResponse, NewBoeking
    from mboek.models.export_import import MatchSuggestion


class Dagboek:
    """A dagboek (journal / sub-ledger) belonging to an administratie.

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds scope context (``_client``, ``_boekjaar_id``) that
    unlocks scope-specific operations such as :py:attr:`boekingen`.

    Obtain a fully-scoped instance via the scope helpers::

        # Both return the same Dagboek type — with all attributes populated:
        dagboek = client.administratie(1).dagboeken.find_by_code("BANK")
        dagboek = client.administratie(1).boekjaar(10).dagboek(code="BANK")

    To add or change scope on an existing object use::

        scoped = dagboek.with_boekjaar(boekjaar_id=10)
        scoped = dagboek.with_boekjaar(name="2024")
        unscoped = scoped.without_boekjaar()

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        code: Short alphanumeric code (e.g. ``"BANK"``).
        naam: Display name.
        dagboek_type: One of ``bank``, ``kas``, ``inkoop``, ``verkoop``, ``memoriaal``.
        grootboekrekening_id: Linked grootboekrekening (e.g. the bank balance account).
        iban: IBAN number of the linked bank account, used for auto-matching during import.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    def __init__(
        self,
        id: int,
        administratie_id: int,
        code: str,
        naam: str,
        dagboek_type: DagboekType,
        grootboekrekening_id: int | None,
        iban: str | None,
        created_at: datetime,
        updated_at: datetime,
        *,
        client: "MboekClient | None" = None,
        boekjaar_id: int | None = None,
    ) -> None:
        self.id = id
        self.administratie_id = administratie_id
        self.code = code
        self.naam = naam
        self.dagboek_type = dagboek_type
        self.grootboekrekening_id = grootboekrekening_id
        self.iban = iban
        self.created_at = created_at
        self.updated_at = updated_at
        self._client = client
        self._boekjaar_id = boekjaar_id

    # ── Scope helpers ─────────────────────────────────────────────────────────

    def with_boekjaar(
        self,
        boekjaar_id: int | None = None,
        *,
        name: str | None = None,
    ) -> "Dagboek":
        """Return a copy of this dagboek with a boekjaar scope added.

        Pass either a numeric ``boekjaar_id`` (no HTTP call) or a ``name``
        to look up the boekjaar by exact name (one HTTP call).

        Args:
            boekjaar_id: Boekjaar ID. No HTTP call is made.
            name: Exact boekjaar name (e.g. ``"2024"``). Requires a client
                reference on this object.

        Returns:
            A new :py:class:`Dagboek` with the boekjaar scope set.

        Raises:
            :py:exc:`ValueError`: Neither or both arguments provided.
            :py:class:`~mboek._exceptions.ScopeError`: ``name`` given but no
                client reference is available on this object.
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` given but
                no matching boekjaar found.
        """
        provided = sum(x is not None for x in [boekjaar_id, name])
        if provided != 1:
            raise ValueError("Provide exactly one of: boekjaar_id, name")
        if name is not None:
            from mboek._exceptions import NotFoundError, ScopeError

            if self._client is None:
                raise ScopeError(
                    "Cannot look up boekjaar by name without a client reference."
                )
            from mboek.resources.boekjaren import BoekjarenResource

            found = BoekjarenResource(self._client, self.administratie_id).find_by_naam(
                name
            )
            if found is None:
                raise NotFoundError(f"Boekjaar '{name}' not found")
            boekjaar_id = found.id
        return Dagboek(
            id=self.id,
            administratie_id=self.administratie_id,
            code=self.code,
            naam=self.naam,
            dagboek_type=self.dagboek_type,
            grootboekrekening_id=self.grootboekrekening_id,
            iban=self.iban,
            created_at=self.created_at,
            updated_at=self.updated_at,
            client=self._client,
            boekjaar_id=boekjaar_id,
        )

    def without_boekjaar(self) -> "Dagboek":
        """Return a copy of this dagboek with the boekjaar scope removed."""
        return Dagboek(
            id=self.id,
            administratie_id=self.administratie_id,
            code=self.code,
            naam=self.naam,
            dagboek_type=self.dagboek_type,
            grootboekrekening_id=self.grootboekrekening_id,
            iban=self.iban,
            created_at=self.created_at,
            updated_at=self.updated_at,
            client=self._client,
            boekjaar_id=None,
        )

    # ── Scoped operations ─────────────────────────────────────────────────────

    @property
    def boekingen(self):
        """Scoped boekingen resource for this dagboek and boekjaar.

        Returns a :py:class:`~mboek.resources._boekjaar_scope.BoekjaarScopedBoekingenResource`
        that exposes :py:meth:`~mboek.resources._boekjaar_scope.BoekjaarScopedBoekingenResource.list`
        and :py:meth:`~mboek.resources._boekjaar_scope.BoekjaarScopedBoekingenResource.create`.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No boekjaar scope set.
                Use :py:meth:`with_boekjaar` first.
        """
        from mboek._exceptions import ScopeError

        if self._boekjaar_id is None:
            raise ScopeError(
                "Accessing boekingen requires a boekjaar scope. "
                "Use .with_boekjaar(boekjaar_id=...) or .with_boekjaar(name=...) first."
            )
        if self._client is None:
            raise ScopeError("Accessing boekingen requires a client reference.")
        from mboek.resources._boekjaar_scope import BoekjaarScopedBoekingenResource

        return BoekjaarScopedBoekingenResource(
            self._client, self.administratie_id, self._boekjaar_id, self.id
        )

    def rerun_regels(self) -> "list[BoekingMetRegelsResponse]":
        """Re-apply all active auto-booking rules to unprocessed boekingen.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError("rerun_regels() requires a client reference.")
        from mboek._parsers import parse_boeking_met_regels

        data = self._client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/rerun-regels",
        )
        if isinstance(data, list):
            return [parse_boeking_met_regels(d) for d in data]
        return []

    def suggest(self, boeking_id: int) -> "list[MatchSuggestion]":
        """Get contra-account suggestions for an unprocessed boeking.

        Args:
            boeking_id: Boeking ID to get suggestions for.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError("suggest() requires a client reference.")
        from mboek._parsers import parse_match_suggestion

        data = self._client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/suggest",
            json={"boeking_id": boeking_id},
        )
        if isinstance(data, list):
            return [parse_match_suggestion(d) for d in data]
        return []

    def import_boekingen(
        self, boekingen: list[dict]
    ) -> "list[BoekingMetRegelsResponse]":
        """Import a list of exported boekingen into this dagboek.

        Args:
            boekingen: List of boeking payloads.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError("import_boekingen() requires a client reference.")
        from mboek._parsers import parse_boeking_met_regels

        data = self._client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/boekingen/import",
            json=boekingen,
        )
        if isinstance(data, list):
            return [parse_boeking_met_regels(d) for d in data]
        return []

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        scope = f", boekjaar_id={self._boekjaar_id}" if self._boekjaar_id else ""
        return f"Dagboek(id={self.id!r}, code={self.code!r}, naam={self.naam!r}{scope})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Dagboek):
            return NotImplemented
        return self.id == other.id and self.administratie_id == other.administratie_id


# Backward-compatible alias.
DagboekResponse = Dagboek


@dataclass
class DagboekWerkStatus:
    """Work-status counts for a dagboek.

    Attributes:
        dagboek_id: ID of the dagboek.
        onverwerkt: Number of boekingen still pointing at the bankimport staging account.
        te_bevestigen: Number of auto-booked entries not yet manually confirmed.
    """

    dagboek_id: int
    onverwerkt: int
    te_bevestigen: int


@dataclass
class NewDagboek:
    """Input for creating a new dagboek.

    At most one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
    ``grootboekrekening_code`` may be provided.  When a name or code is supplied
    the resource layer resolves it to an ID before sending the request.

    Attributes:
        code: Short code (e.g. ``"BANK"``).
        naam: Display name.
        dagboek_type: Journal type.
        grootboekrekening_id: Optional linked balance account (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        iban: Optional IBAN for bank-statement auto-matching.
    """

    code: str
    naam: str
    dagboek_type: DagboekType
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    iban: str | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        d: dict = {
            "code": self.code,
            "naam": self.naam,
            "dagboek_type": self.dagboek_type.value,
        }
        if self.grootboekrekening_id is not None:
            d["grootboekrekening_id"] = self.grootboekrekening_id
        if self.iban is not None:
            d["iban"] = self.iban
        return d


@dataclass
class UpdateDagboek:
    """Input for partially updating a dagboek.

    All fields optional.  At most one of ``grootboekrekening_id``,
    ``grootboekrekening_naam``, or ``grootboekrekening_code`` may be provided.
    When a name or code is supplied the resource layer resolves it to an ID
    before sending the request.

    Attributes:
        code: New short code.
        naam: New display name.
        dagboek_type: New journal type.
        grootboekrekening_id: New linked balance account (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        iban: New IBAN.
    """

    code: str | None = None
    naam: str | None = None
    dagboek_type: DagboekType | None = None
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    iban: str | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.code is not None:
            d["code"] = self.code
        if self.naam is not None:
            d["naam"] = self.naam
        if self.dagboek_type is not None:
            d["dagboek_type"] = self.dagboek_type.value
        if self.grootboekrekening_id is not None:
            d["grootboekrekening_id"] = self.grootboekrekening_id
        if self.iban is not None:
            d["iban"] = self.iban
        return d
