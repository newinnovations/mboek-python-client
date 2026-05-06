"""Dagboek (journal / sub-ledger) models."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from mboek._exceptions import MboekError
from mboek.models._enums import DagboekType

if TYPE_CHECKING:
    from mboek._client import MboekClient
    from mboek.models.export_import import (
        BoekingenImportResult,
        BoekingExport,
        MatchSuggestion,
    )
    from mboek.resources._boekjaar_scope import BoekjaarScopedBoekingenResource


class Dagboek:
    """A dagboek (journal / sub-ledger) belonging to an administratie.

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds scope context (``_client``, ``_boekjaar_id``) that
    unlocks scope-specific operations such as :py:attr:`boekingen`.

    Obtain a fully-scoped instance via the scope helpers::

        # Both return the same Dagboek type — with all attributes populated:
        dagboek = client.administratie(1).dagboeken.list(code="BANK")[0]
        dagboek = client.administratie(1).boekjaar(10).dagboek(code="BANK")

    To add or change scope on an existing object use::

        scoped = dagboek.with_boekjaar(id=10)
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
        id: int | None = None,
        *,
        name: str | None = None,
    ) -> "Dagboek":
        """Return a copy of this dagboek with a boekjaar scope added.

        Pass either a numeric ``id`` (no HTTP call) or a ``name``
        to look up the boekjaar by exact name (one HTTP call).

        Args:
            id: Boekjaar ID. No HTTP call is made.
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
            boekjaar_id=id,
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

    def _require_client(self, operation: str) -> "MboekClient":
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError(f"{operation} requires a client reference.")
        return self._client

    def _resolve_import_boekjaar_id(
        self,
        *,
        boekjaar_id: int | None = None,
        boekjaar_name: str | None = None,
    ) -> int:
        from mboek._exceptions import ScopeError
        from mboek.resources.boekjaren import BoekjarenResource

        provided = sum(x is not None for x in [boekjaar_id, boekjaar_name])
        if provided > 1:
            raise ValueError("Provide only one of: boekjaar_id, boekjaar_name")
        if boekjaar_id is not None:
            return boekjaar_id
        if boekjaar_name is not None:
            client = self._require_client("import_boekingen()")
            boekjaren = BoekjarenResource(client, self.administratie_id)
            found = boekjaren._require_single_match(
                boekjaren.list(name=boekjaar_name),
                not_found_message=f"Boekjaar '{boekjaar_name}' not found",
                multiple_message=f"Multiple boekjaren named '{boekjaar_name}' found",
            )
            return found.id
        if self._boekjaar_id is None:
            raise ScopeError(
                "import_boekingen() requires a boekjaar scope or an explicit "
                "boekjaar_id/boekjaar_name."
            )
        return self._boekjaar_id

    @staticmethod
    def _require_list_response(data: Any, *, operation: str) -> list[dict]:
        if not isinstance(data, list):
            raise MboekError(f"{operation} expected a JSON array response", detail=data)
        return data

    @staticmethod
    def _require_dict_response(data: Any, *, operation: str) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise MboekError(
                f"{operation} expected a JSON object response", detail=data
            )
        return data

    @property
    def boekingen(self) -> "BoekjaarScopedBoekingenResource":
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
                "Use .with_boekjaar(id=...) or .with_boekjaar(name=...) first."
            )
        if self._client is None:
            raise ScopeError("Accessing boekingen requires a client reference.")
        from mboek.resources._boekjaar_scope import BoekjaarScopedBoekingenResource

        return BoekjaarScopedBoekingenResource(
            self._client, self.administratie_id, self._boekjaar_id, self.id
        )

    def rerun_regels(self) -> int:
        """Re-apply all active auto-booking rules to unprocessed boekingen.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("rerun_regels()")
        data = client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/rerun-regels",
        )
        payload = self._require_dict_response(data, operation="rerun_regels()")
        updated = payload.get("updated")
        if not isinstance(updated, int):
            raise MboekError(
                "rerun_regels() expected an integer 'updated' field",
                detail=payload,
            )
        return updated

    def suggest(
        self,
        omschrijving: str,
        *,
        tegenpartij_iban: "str | None" = None,
        tegenpartij_naam: "str | None" = None,
    ) -> "list[MatchSuggestion]":
        """Get contra-account suggestions for a bank transaction description.

        Looks up previously used contra-accounts for similar transactions in
        this dagboek and ranks them by frequency of use.

        Args:
            omschrijving: Transaction description to match against prior boekingen.
            tegenpartij_iban: Optional counterparty IBAN to refine matching.
            tegenpartij_naam: Optional counterparty name to refine matching.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("suggest()")
        from mboek._parsers import parse_match_suggestion

        body: dict = {"omschrijving": omschrijving}
        if tegenpartij_iban is not None:
            body["tegenpartij_iban"] = tegenpartij_iban
        if tegenpartij_naam is not None:
            body["tegenpartij_naam"] = tegenpartij_naam

        data = client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/suggest",
            json=body,
        )
        payload = self._require_list_response(data, operation="suggest()")
        try:
            return [parse_match_suggestion(d) for d in payload]
        except (KeyError, TypeError, ValueError) as exc:
            raise MboekError(
                "suggest() returned an unexpected response payload",
                detail=payload,
            ) from exc

    def import_boekingen(
        self,
        boekingen: Sequence["BoekingExport"],
        *,
        boekjaar_id: int | None = None,
        boekjaar_name: str | None = None,
    ) -> "BoekingenImportResult":
        """Import a list of exported boekingen into this dagboek.

        Args:
            boekingen: Export payloads, typically obtained from
                :py:meth:`mboek.resources.export_import.AdminExportImportResource.export_boeking`
                or loaded from JSON with
                :py:meth:`mboek.models.export_import.BoekingExport.from_dict`.
            boekjaar_id: Target boekjaar ID. When omitted, the current
                boekjaar scope is used.
            boekjaar_name: Target boekjaar name. Requires a client reference.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
        """
        client = self._require_client("import_boekingen()")
        from mboek._parsers import parse_boekingen_import_result

        resolved_boekjaar_id = self._resolve_import_boekjaar_id(
            boekjaar_id=boekjaar_id,
            boekjaar_name=boekjaar_name,
        )
        data = client._request(
            "POST",
            f"/api/administraties/{self.administratie_id}/dagboeken/{self.id}/boekingen/import",
            params={"boekjaar_id": resolved_boekjaar_id},
            json={"boekingen": [boeking.to_dict() for boeking in boekingen]},
        )
        payload = self._require_dict_response(data, operation="import_boekingen()")
        try:
            return parse_boekingen_import_result(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise MboekError(
                "import_boekingen() returned an unexpected response payload",
                detail=payload,
            ) from exc

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        scope = f", boekjaar_id={self._boekjaar_id}" if self._boekjaar_id else ""
        return f"Dagboek(id={self.id!r}, code={self.code!r}, naam={self.naam!r}{scope})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Dagboek):
            return NotImplemented
        return self.id == other.id and self.administratie_id == other.administratie_id


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
