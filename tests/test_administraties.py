"""Tests for the administraties resource."""

from __future__ import annotations

import responses

from mboek._exceptions import ForbiddenError, NotFoundError
from tests.conftest import ADMINISTRATIE, BASE_URL


def test_list(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    items = client.administraties.list()
    assert len(items) == 1
    assert items[0].id == 1
    assert items[0].naam == "Test BV"


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1", json=ADMINISTRATIE
    )
    item = client.administraties.get(1)
    assert item.naam == "Test BV"


def test_get_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/999", json={"error": "Not found"}, status=404
    )
    try:
        client.administraties.get(999)
        assert False
    except NotFoundError as e:
        assert e.status_code == 404


def test_get_forbidden(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/2", json={"error": "Forbidden"}, status=403
    )
    try:
        client.administraties.get(2)
        assert False
    except ForbiddenError:
        pass


def test_create(mocked_responses, client):
    from mboek import CreateAdministratieInput

    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/administraties", json=ADMINISTRATIE, status=201
    )
    inp = CreateAdministratieInput(naam="Test BV")
    item = client.administraties.create(inp)
    assert item.id == 1


def test_update(mocked_responses, client):
    from mboek import UpdateAdministratieInput

    updated = {**ADMINISTRATIE, "naam": "Gewijzigd BV"}
    mocked_responses.add(
        responses.PATCH, f"{BASE_URL}/api/administraties/1", json=updated
    )
    inp = UpdateAdministratieInput(naam="Gewijzigd BV")
    item = client.administraties.update(1, inp)
    assert item.naam == "Gewijzigd BV"


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1", status=204
    )
    client.administraties.delete(1)  # should not raise


def test_find_by_naam_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    result = client.administraties.find_by_naam("Test BV")
    assert result is not None
    assert result.id == 1


def test_find_by_naam_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    result = client.administraties.find_by_naam("Nonexistent")
    assert result is None
