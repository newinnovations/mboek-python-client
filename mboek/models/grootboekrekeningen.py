"""Grootboekrekening (chart of accounts) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from mboek.models._enums import RekeningCategorie, RekeningType

if TYPE_CHECKING:
    from mboek._client import MboekClient


class Grootboekrekening:
    """A general-ledger account (grootboekrekening).

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds scope context (``_client``, ``_boekjaar_id``) that
    unlocks scope-specific operations such as :py:attr:`saldo` and
    :py:meth:`mutaties`.

    When obtained via a boekjaar scope (e.g.
    :py:meth:`~mboek.models.boekjaren.Boekjaar.grootboekrekening`) the
    ``saldo`` and ``aantal_transacties`` are populated immediately from the
    API response.  When obtained without a boekjaar scope, accessing
    :py:attr:`saldo` raises :py:class:`~mboek._exceptions.ScopeError`.

    Use :py:meth:`with_boekjaar` to add a boekjaar scope; the saldo is then
    lazy-fetched on first access::

        gbr = client.administratie(1).grootboekrekeningen.list(code="1220")[0]
        gbr_scoped = gbr.with_boekjaar(id=10)
        print(gbr_scoped.saldo)   # one HTTP call here; result is cached

    Attributes:
        id: Unique database identifier.
        administratie_id: ID of the owning administratie.
        code: Account code (e.g. ``"1220"``).
        naam: Account name (e.g. ``"Bank"``).
        rekening_type: Account type.
        categorie: Statement category.
        rgs_code: Optional Dutch RGS code.
        parent_id: Optional ID of a parent account.
        default_btw_id: Default BTW code for this account.
        actief: Whether this account is active.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    def __init__(
        self,
        id: int,
        administratie_id: int,
        code: str,
        naam: str,
        rekening_type: RekeningType,
        categorie: RekeningCategorie,
        rgs_code: str | None,
        parent_id: int | None,
        default_btw_id: int | None,
        actief: bool,
        created_at: datetime,
        updated_at: datetime,
        *,
        client: "MboekClient | None" = None,
        boekjaar_id: int | None = None,
        saldo: Decimal | None = None,
        aantal_transacties: int | None = None,
    ) -> None:
        self.id = id
        self.administratie_id = administratie_id
        self.code = code
        self.naam = naam
        self.rekening_type = rekening_type
        self.categorie = categorie
        self.rgs_code = rgs_code
        self.parent_id = parent_id
        self.default_btw_id = default_btw_id
        self.actief = actief
        self.created_at = created_at
        self.updated_at = updated_at
        self._client = client
        self._boekjaar_id = boekjaar_id
        self._saldo = saldo
        self._aantal_transacties = aantal_transacties

    # ── Scope helpers ─────────────────────────────────────────────────────────

    def with_boekjaar(
        self,
        id: int | None = None,
        *,
        name: str | None = None,
    ) -> "Grootboekrekening":
        """Return a copy of this rekening with a boekjaar scope added.

        The :py:attr:`saldo` is lazy-fetched from the API on first access
        after scoping (unless it was already available).

        Args:
            id: Boekjaar ID. No HTTP call is made.
            name: Exact boekjaar name (e.g. ``"2024"``). Requires a client
                reference.

        Returns:
            A new :py:class:`Grootboekrekening` with the boekjaar scope set.

        Raises:
            :py:exc:`ValueError`: Neither or both arguments provided.
            :py:class:`~mboek._exceptions.ScopeError`: ``name`` given but no
                client reference is available.
            :py:class:`~mboek._exceptions.NotFoundError`: ``name`` given but
                no matching boekjaar found.
        """
        provided = sum(x is not None for x in [id, name])
        if provided != 1:
            raise ValueError("Provide exactly one of: id, name")
        if name is not None:
            from mboek._exceptions import ScopeError

            if self._client is None:
                raise ScopeError(
                    "Cannot look up boekjaar by name without a client reference."
                )
            from mboek.resources.boekjaren import BoekjarenResource

            boekjaren = BoekjarenResource(self._client, self.administratie_id)
            found = boekjaren._require_single_match(
                boekjaren.list(name=name),
                not_found_message=f"Boekjaar '{name}' not found",
                multiple_message=f"Multiple boekjaren named '{name}' found",
            )
            id = found.id
        return Grootboekrekening(
            id=self.id,
            administratie_id=self.administratie_id,
            code=self.code,
            naam=self.naam,
            rekening_type=self.rekening_type,
            categorie=self.categorie,
            rgs_code=self.rgs_code,
            parent_id=self.parent_id,
            default_btw_id=self.default_btw_id,
            actief=self.actief,
            created_at=self.created_at,
            updated_at=self.updated_at,
            client=self._client,
            boekjaar_id=id,
            # saldo not carried over — will be lazy-fetched for the new boekjaar
        )

    def without_boekjaar(self) -> "Grootboekrekening":
        """Return a copy of this rekening with the boekjaar scope removed."""
        return Grootboekrekening(
            id=self.id,
            administratie_id=self.administratie_id,
            code=self.code,
            naam=self.naam,
            rekening_type=self.rekening_type,
            categorie=self.categorie,
            rgs_code=self.rgs_code,
            parent_id=self.parent_id,
            default_btw_id=self.default_btw_id,
            actief=self.actief,
            created_at=self.created_at,
            updated_at=self.updated_at,
            client=self._client,
            boekjaar_id=None,
        )

    # ── Scoped properties ─────────────────────────────────────────────────────

    @property
    def saldo(self) -> Decimal:
        """Net balance in euros for the scoped boekjaar (positive = debet).

        When obtained via a boekjaar scope, the value is already populated.
        When added via :py:meth:`with_boekjaar`, the value is lazy-fetched
        from the API on first access (and cached).

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No boekjaar scope set.
        """
        if self._saldo is not None:
            return self._saldo
        self._fetch_saldo()
        if self._saldo is None:
            raise AssertionError(
                "saldo could not be resolved for the scoped grootboekrekening"
            )
        return self._saldo

    @property
    def aantal_transacties(self) -> int:
        """Number of boekingsregels in the scoped boekjaar.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No boekjaar scope set.
        """
        if self._aantal_transacties is not None:
            return self._aantal_transacties
        self._fetch_saldo()
        if self._aantal_transacties is None:
            raise AssertionError(
                "aantal_transacties could not be resolved for the scoped grootboekrekening"
            )
        return self._aantal_transacties

    @property
    def transacties(self) -> int:
        """Alias for :py:attr:`aantal_transacties`."""
        return self.aantal_transacties

    def _fetch_saldo(self) -> None:
        """Lazy-fetch saldo and aantal_transacties from the met-saldo endpoint."""
        from mboek._exceptions import ScopeError

        if self._boekjaar_id is None:
            raise ScopeError(
                "saldo requires a boekjaar scope. "
                "Use .with_boekjaar(id=...) or .with_boekjaar(name=...) first."
            )
        if self._client is None:
            raise ScopeError("saldo requires a client reference.")
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        rekeningen = GrootboekrekeningenResource(
            self._client, self.administratie_id
        ).met_saldo(self._boekjaar_id)
        match = next((r for r in rekeningen if r.id == self.id), None)
        if match is None:
            self._saldo = Decimal(0)
            self._aantal_transacties = 0
        else:
            self._saldo = match._saldo
            self._aantal_transacties = match._aantal_transacties

    # ── Scoped methods ────────────────────────────────────────────────────────

    def mutaties(
        self, *, limit: int | None = None, offset: int | None = None
    ) -> "list[GrootboekMutatie]":
        """Return the full mutation ledger for this rekening in the scoped boekjaar.

        Args:
            limit: Maximum number of mutaties to return. When omitted, all
                backend pages are fetched automatically.
            offset: Number of mutaties to skip before collecting results.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No boekjaar scope or
                no client reference.
        """
        from mboek._exceptions import ScopeError

        if self._boekjaar_id is None:
            raise ScopeError(
                "mutaties() requires a boekjaar scope. "
                "Use .with_boekjaar(id=...) first."
            )
        if self._client is None:
            raise ScopeError("mutaties() requires a client reference.")
        from mboek.resources.grootboekrekeningen import GrootboekrekeningenResource

        return GrootboekrekeningenResource(
            self._client, self.administratie_id
        ).mutaties(self.id, self._boekjaar_id, limit=limit, offset=offset)

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        scope = f", boekjaar_id={self._boekjaar_id}" if self._boekjaar_id else ""
        return (
            f"Grootboekrekening(id={self.id!r}, code={self.code!r},"
            f" naam={self.naam!r}{scope})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Grootboekrekening):
            return NotImplemented
        return self.id == other.id and self.administratie_id == other.administratie_id


@dataclass
class GrootboekMutatie:
    """A single mutation (boekingsregel) in the account ledger.

    Attributes:
        regel_id: ID of the boekingsregel.
        boeking_id: ID of the parent boeking.
        dagboek_id: ID of the dagboek.
        datum: Booking date.
        dagboek_code: Short code of the dagboek (e.g. ``"BANK"``).
        dagboek_naam: Name of the dagboek.
        boeking_omschrijving: Description of the parent boeking.
        regel_omschrijving: Description of this specific regel.
        bedrag: Amount in euros (positive = debet, negative = credit).
    """

    regel_id: int
    boeking_id: int
    dagboek_id: int
    datum: str
    dagboek_code: str
    dagboek_naam: str
    boeking_omschrijving: str
    regel_omschrijving: str
    bedrag: Decimal
