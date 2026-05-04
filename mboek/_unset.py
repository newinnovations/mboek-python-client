"""Internal sentinel used to distinguish omitted PATCH fields from explicit ``None``."""

from __future__ import annotations


class UnsetType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET = UnsetType()
