"""Export / import and bank-import suggestion models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, ClassVar, Type, TypeVar

ExportPayloadT = TypeVar("ExportPayloadT", bound="_BaseExportPayload")


@dataclass
class _BaseExportPayload:
    _payload: dict[str, Any] = field(repr=False)
    _expected_type: ClassVar[str]

    def __post_init__(self) -> None:
        if not isinstance(self._payload, dict):
            raise TypeError(f"{self.__class__.__name__} payload must be a dict")
        payload_type = self._payload.get("type")
        if payload_type != self._expected_type:
            raise ValueError(
                f"{self.__class__.__name__} requires payload type "
                f"{self._expected_type!r}, got {payload_type!r}"
            )

    @classmethod
    def from_dict(cls: Type[ExportPayloadT], payload: dict[str, Any]) -> ExportPayloadT:
        if not isinstance(payload, dict):
            raise TypeError(f"{cls.__name__} payload must be a dict")
        return cls(_payload=deepcopy(payload))

    @property
    def type(self) -> str:
        return self._expected_type

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._payload)


@dataclass
class AdministratieExport(_BaseExportPayload):
    """Full administratie JSON export payload."""

    _expected_type: ClassVar[str] = "administratie"


@dataclass
class BoekjaarExport(_BaseExportPayload):
    """Single-boekjaar JSON export payload."""

    _expected_type: ClassVar[str] = "boekjaar"


@dataclass
class BoekingExport(_BaseExportPayload):
    """Single-boeking JSON export payload."""

    _expected_type: ClassVar[str] = "boeking"

    @property
    def id(self) -> int | None:
        value = self._payload.get("id")
        if value is None:
            return None
        if not isinstance(value, int):
            raise ValueError(
                f"BoekingExport id must be an int when present, got {type(value).__name__}"
            )
        return value


@dataclass
class AdministratieImportResult:
    """Result of importing an administratie export payload."""

    administratie_id: int
    naam: str
    boekingen_imported: int


@dataclass
class BoekjaarImportResult:
    """Result of importing a boekjaar export payload."""

    boekjaar_id: int
    naam: str
    boekingen_imported: int


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
    contra_rekening_code: int
    contra_rekening_naam: str
    confidence: int
    reason: str

    def __post_init__(self) -> None:
        if self.confidence < 0:
            raise ValueError(f"confidence must be >= 0, got {self.confidence}")
