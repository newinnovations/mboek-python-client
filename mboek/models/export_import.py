"""Export / import and bank-import suggestion models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImportResult:
    """Result of a bank statement import.

    Attributes:
        imported: Number of transactions imported.
        duplicates_skipped: Number of duplicate transactions skipped.
        zero_bedrag_skipped: Number of zero-amount transactions skipped.
        boekjaar_niet_gevonden_skipped: Number of transactions skipped because
            no boekjaar could be determined.
        auto_geboekt: Number of imported transactions that were auto-booked by
            matching rules.
        unmatched_ibans: IBANs from the statement that did not match a dagboek.
        parse_warnings: Optional warnings produced while parsing the statement.
    """

    imported: int
    duplicates_skipped: int
    zero_bedrag_skipped: int
    boekjaar_niet_gevonden_skipped: int
    auto_geboekt: int
    unmatched_ibans: list[str]
    parse_warnings: list[str] | None = None


@dataclass
class BoekingenImportResult:
    """Result of importing exported boekingen into a dagboek.

    Attributes:
        dagboek_id: Target dagboek ID.
        boekingen_imported: Number of boekingen inserted.
    """

    dagboek_id: int
    boekingen_imported: int


@dataclass
class MatchSuggestion:
    """A suggested contra account for an unprocessed bank transaction.

    The suggestion engine looks at previous bookings from the same counterparty
    to propose the most likely contra account.

    Attributes:
        contra_rekening_id: Suggested contra-account ID.
        contra_rekening_code: Contra-account code.
        contra_rekening_naam: Contra-account name.
        confidence: Non-negative confidence score.
        reason: Explanation of why the suggestion was returned.
    """

    contra_rekening_id: int
    contra_rekening_code: str
    contra_rekening_naam: str
    confidence: int
    reason: str

    def __post_init__(self) -> None:
        if self.confidence < 0:
            raise ValueError(f"confidence must be >= 0, got {self.confidence}")
