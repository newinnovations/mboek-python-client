"""Export / import and bank-import suggestion models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


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
class MatchSuggestion:
    """A suggested contra account for an unprocessed bank transaction.

    The suggestion engine looks at previous bookings from the same counterparty
    to propose the most likely contra account.

    Attributes:
        grootboekrekening_id: Suggested account ID.
        code: Account code.
        naam: Account name.
        btw_code_id: Suggested BTW code (if any).
        btw_code: Short BTW code string.
        confidence: Confidence score (0–1).
    """

    grootboekrekening_id: int
    code: str
    naam: str
    btw_code_id: int | None
    btw_code: str | None
    confidence: Decimal

    def __post_init__(self) -> None:
        if not (0 <= self.confidence <= 1):
            raise ValueError(
                f"confidence must be between 0 and 1, got {self.confidence}"
            )
