"""Tests for models package public API consistency."""

from __future__ import annotations

import mboek
import mboek.models as models_pkg
from mboek._client import MboekClient
from mboek.models.boekjaren import Boekjaar
from mboek.models.dagboeken import Dagboek


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


def test_top_level_reexports_include_advanced_enums():
    assert hasattr(mboek, "AutoBookingBedragType")
    assert hasattr(mboek, "BoekingStatus")
    assert "AutoBookingBedragType" in mboek.__all__
    assert "BoekingStatus" in mboek.__all__


def test_top_level_reexports_include_auto_booking_apply_result():
    assert hasattr(mboek, "AutoBookingRuleApplicationResult")
    assert "AutoBookingRuleApplicationResult" in mboek.__all__


def test_top_level_reexports_include_new_typed_payload_models():
    for name in [
        "AdministratieExport",
        "AdministratieImportResult",
        "JaarrekeningHtmlReport",
        "JaarrekeningLogLevel",
        "JaarrekeningPdfReport",
        "JaarrekeningRuntimeMessage",
        "BoekingExport",
        "BoekjaarExport",
        "BoekjaarImportResult",
        "CurrentUser",
        "VacuumResult",
    ]:
        assert hasattr(mboek, name)
        assert name in mboek.__all__


def test_resource_properties_have_explicit_return_annotations():
    properties = [
        MboekClient.auth,
        MboekClient.administraties,
        MboekClient.boekingen,
        MboekClient.export_import,
        MboekClient.jaarrekening,
        MboekClient.maintenance,
        Boekjaar.reports,
        Boekjaar.btw_aangifte,
        Dagboek.boekingen,
    ]

    for prop in properties:
        assert prop.fget is not None
        assert "return" in prop.fget.__annotations__
