"""Maintenance operation models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VacuumResult:
    """Result of a database vacuum operation.

    Attributes:
        message: Human-readable completion message from the backend.
        elapsed_ms: Optional runtime reported by the backend in milliseconds.
    """

    message: str
    elapsed_ms: int | None = None
