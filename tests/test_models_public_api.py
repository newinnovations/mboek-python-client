"""Tests for models package public API consistency."""

from __future__ import annotations

import mboek.models as models_pkg


def test_all_names_are_importable():
    """Every name declared in models.__all__ must be importable from the package."""
    for name in models_pkg.__all__:
        assert hasattr(
            models_pkg, name
        ), f"{name!r} is listed in mboek.models.__all__ but not importable"


def test_all_names_are_public():
    """No name in __all__ should start with an underscore."""
    for name in models_pkg.__all__:
        assert not name.startswith("_"), f"{name!r} is in __all__ but starts with '_'"


def test_all_entries_are_unique():
    """__all__ should not contain duplicates."""
    assert len(models_pkg.__all__) == len(
        set(models_pkg.__all__)
    ), "mboek.models.__all__ contains duplicate entries"
