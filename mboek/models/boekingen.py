"""Boeking (journal entry) and boekingsregel (entry line) models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from mboek.models._enums import BoekingStatus, Regeltype


@dataclass
class BoekingsregelResponse:
    """A single line of a journal entry.

    Attributes:
        id: Unique database identifier.
        boeking_id: ID of the parent boeking.
        grootboekrekening_id: The general-ledger account debited/credited.
        omschrijving: Line description.
        bedrag: Amount in euros (positive = debet, negative = credit).
        btw_code_id: Optional BTW code applied to this line.
        regeltype: ``netto`` for the base amount, ``btw`` for the VAT component.
        netto_id: For BTW lines, the ID of the associated netto line.
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


@dataclass
class BoekingResponse:
    """A journal entry (boeking).

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
        created_at: Creation timestamp (UTC).
        updated_at: Last-update timestamp (UTC).
    """

    id: int
    dagboek_id: int
    boekjaar_id: int
    datum: date
    omschrijving: str
    stuknummer: str | None
    status: BoekingStatus
    tegenpartij_naam: str | None
    tegenpartij_iban: str | None
    referentie_import: str | None
    import_hash: str | None
    auto_geboekt: bool
    gecontroleerd: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class BoekingMetRegelsResponse:
    """A boeking together with all its boekingsregels.

    Attributes:
        boeking: The journal entry header.
        regels: The individual debit/credit lines.
    """

    boeking: BoekingResponse
    regels: list[BoekingsregelResponse]


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
        regeltype: ``netto`` (default) or ``btw``.
        netto_ref: For BTW lines, the index (0-based) of the corresponding netto
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
