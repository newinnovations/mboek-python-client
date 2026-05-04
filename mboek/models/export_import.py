"""Export / import and bank-import suggestion models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImportResult:
    """Result of a bank statement import.

    Attributes:
        imported: Number of transactions imported.
        skipped: Number of transactions skipped (duplicates or already imported).
        boeking_ids: IDs of the created boekingen.
    """

    imported: int
    skipped: int
    boeking_ids: list[int]


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
