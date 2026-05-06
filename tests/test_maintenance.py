"""Tests for maintenance operations."""

from __future__ import annotations

import responses

from mboek import VacuumResult
from tests.conftest import BASE_URL


def test_vacuum_returns_typed_result(mocked_responses, client):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/vacuum",
        json={"message": "VACUUM completed", "elapsed_ms": 17},
    )

    result = client.maintenance.vacuum()

    assert isinstance(result, VacuumResult)
    assert result.message == "VACUUM completed"
    assert result.elapsed_ms == 17
