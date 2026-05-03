"""Boeking (journal entry) and boekingsregel (entry line) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from mboek.models._enums import BoekingStatus, Regeltype

if TYPE_CHECKING:
    from mboek._client import MboekClient


@dataclass
class Boekingsregel:
    """A single line of a journal entry.

    Attributes:
        id: Unique database identifier.
        boeking_id: ID of the parent boeking.
        grootboekrekening_id: The general-ledger account debited/credited.
        omschrijving: Line description.
        bedrag: Amount in euros (positive = debet, negative = credit).
        btw_code_id: Optional BTW code applied to this line.
        regeltype: ``netto`` for the base amount, ``btw_output`` or
            ``btw_input`` for the VAT component.
        netto_id: For VAT lines, the ID of the associated netto line.
        created_at: Creation timestamp (UTC).
    """

    id: int
    boeking_id: int
    grootboekrekening_id: int
    omschrijving: str
    bedrag: Decimal
    btw_code_id: int | None
    regeltype: Regeltype
    netto_id: int | None
    created_at: datetime


class Boeking:
    """A journal entry (boeking) with all its boekingsregels.

    This is a *rich domain object*: it always carries all data attributes and
    optionally holds a client reference (``_client``) that unlocks instance-level
    operations such as :py:meth:`delete` and :py:meth:`update`.

    Obtain a scoped instance via any resource call::

        boeking = client.boekingen.get(100)
        boeking.update(omschrijving="Corrected description")
        boeking.delete()

    Attributes:
        id: Unique database identifier.
        dagboek_id: ID of the dagboek this entry belongs to.
        boekjaar_id: ID of the fiscal year.
        datum: Booking date.
        omschrijving: Description.
        stuknummer: Optional document/invoice reference number.
        status: ``concept`` or ``definitief``.
        tegenpartij_naam: Optional counterparty name (from bank import).
        tegenpartij_iban: Optional counterparty IBAN (from bank import).
        referentie_import: Optional import reference (from bank statement).
        import_hash: Hash used to deduplicate bank imports.
        auto_geboekt: ``True`` when booked by an automatic rule (shows ⚡ in the UI).
        gecontroleerd: ``True`` when manually reviewed/confirmed.
        regels: The individual debit/credit lines.
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    def __init__(
        self,
        id: int,
        dagboek_id: int,
        boekjaar_id: int,
        datum: date,
        omschrijving: str,
        stuknummer: str | None,
        status: BoekingStatus,
        tegenpartij_naam: str | None,
        tegenpartij_iban: str | None,
        referentie_import: str | None,
        import_hash: str | None,
        auto_geboekt: bool,
        gecontroleerd: bool,
        created_at: datetime,
        regels: list[Boekingsregel],
        updated_at: datetime,
        *,
        client: "MboekClient | None" = None,
    ) -> None:
        self.id = id
        self.dagboek_id = dagboek_id
        self.boekjaar_id = boekjaar_id
        self.datum = datum
        self.omschrijving = omschrijving
        self.stuknummer = stuknummer
        self.status = status
        self.tegenpartij_naam = tegenpartij_naam
        self.tegenpartij_iban = tegenpartij_iban
        self.referentie_import = referentie_import
        self.import_hash = import_hash
        self.auto_geboekt = auto_geboekt
        self.gecontroleerd = gecontroleerd
        self.created_at = created_at
        self.regels = regels
        self.updated_at = updated_at
        self._client = client

    # ── Internal scope guard ─────────────────────────────────────────────────

    def _require_client(self, operation: str) -> "MboekClient":
        from mboek._exceptions import ScopeError

        if self._client is None:
            raise ScopeError(
                f"{operation} requires a client reference. "
                "Obtain the boeking via a resource call (e.g. client.boekingen.get(...))."
            )
        return self._client

    # ── Instance-level operations ─────────────────────────────────────────────

    def delete(self) -> None:
        """Permanently delete this boeking and all its boekingsregels.

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
            :py:class:`~mboek._exceptions.NotFoundError`: Boeking not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        client = self._require_client("delete()")
        from mboek.resources.boekingen import BoekingenResource

        BoekingenResource(client).delete(self.id)

    def update(
        self,
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
    ) -> "Boeking":
        """Update this boeking's header fields and optionally replace all regels.

        If ``regels`` is provided the existing regels are deleted and the new
        set is inserted atomically. Manually editing regels automatically
        clears the ``auto_geboekt`` and ``gecontroleerd`` flags.

        Args:
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
            The updated boeking (a fresh instance).

        Raises:
            :py:class:`~mboek._exceptions.ScopeError`: No client reference.
            :py:class:`~mboek._exceptions.NotFoundError`: Boeking not found.
            :py:class:`~mboek._exceptions.ForbiddenError`: Not the owner.
        """
        client = self._require_client("update()")
        from mboek.resources.boekingen import BoekingenResource

        return BoekingenResource(client).update(
            self.id,
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

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Boeking(id={self.id!r}, datum={self.datum!r},"
            f" omschrijving={self.omschrijving!r}, status={self.status!r})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Boeking):
            return NotImplemented
        return self.id == other.id


@dataclass
class NewBoekingsregel:
    """A single line for a new or updated boeking.

    All regels together must balance: ``sum(bedrag) == 0``.

    Exactly one of ``grootboekrekening_id``, ``grootboekrekening_naam``, or
    ``grootboekrekening_code`` must be provided.  When a name or code is
    supplied the resource layer resolves it to an ID before sending the request.

    Attributes:
        omschrijving: Line description.
        bedrag: Amount in euros (positive = debet, negative = credit).
        grootboekrekening_id: Account to debit/credit (numeric ID).
        grootboekrekening_naam: Account name — alternative to ``grootboekrekening_id``.
        grootboekrekening_code: Account code — alternative to ``grootboekrekening_id``.
        btw_code_id: Optional BTW code.
        regeltype: ``netto`` (default), ``btw_output``, or ``btw_input``.
        netto_ref: For VAT lines, the index (0-based) of the corresponding netto
            line in the same ``regels`` list.
    """

    omschrijving: str
    bedrag: Decimal
    grootboekrekening_id: int | None = None
    grootboekrekening_naam: str | None = None
    grootboekrekening_code: str | None = None
    btw_code_id: int | None = None
    regeltype: Regeltype = Regeltype.NETTO
    netto_ref: int | None = None

    def __post_init__(self) -> None:
        provided = sum(
            x is not None
            for x in [
                self.grootboekrekening_id,
                self.grootboekrekening_naam,
                self.grootboekrekening_code,
            ]
        )
        if provided == 0:
            raise ValueError(
                "Provide exactly one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )
        if provided > 1:
            raise ValueError(
                "Provide only one of: grootboekrekening_id, grootboekrekening_naam, grootboekrekening_code"
            )

    def to_dict(self) -> dict:
        if self.grootboekrekening_id is None:
            raise ValueError(
                "grootboekrekening_id is not yet resolved; the resource should have resolved "
                "grootboekrekening_naam / grootboekrekening_code before calling to_dict()"
            )
        d: dict = {
            "grootboekrekening_id": self.grootboekrekening_id,
            "omschrijving": self.omschrijving,
            "bedrag": int(self.bedrag * 100),  # convert euros → cents
            "regeltype": self.regeltype.value,
        }
        if self.btw_code_id is not None:
            d["btw_code_id"] = self.btw_code_id
        if self.netto_ref is not None:
            d["netto_ref"] = self.netto_ref
        return d
