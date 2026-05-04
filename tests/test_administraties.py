"""Tests for the administraties resource."""

from __future__ import annotations

import pytest
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
    admin_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/administraties")
    ]
    assert "limit=1000" in admin_calls[-1].request.url
    assert "offset=0" in admin_calls[-1].request.url


def test_get(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties/1", json=ADMINISTRATIE
    )
    item = client.administraties.get(1)
    assert item.naam == "Test BV"


def test_get_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/999",
        json={"error": "Not found"},
        status=404,
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administraties.get(999)
    assert exc_info.value.status_code == 404


def test_get_forbidden(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties/2",
        json={"error": "Forbidden"},
        status=403,
    )
    with pytest.raises(ForbiddenError):
        client.administraties.get(2)


def test_create(mocked_responses, client):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/administraties", json=ADMINISTRATIE, status=201
    )
    item = client.administraties.create(naam="Test BV")
    assert item.id == 1


def test_update(mocked_responses, client):
    updated = {**ADMINISTRATIE, "naam": "Gewijzigd BV"}
    mocked_responses.add(
        responses.PATCH, f"{BASE_URL}/api/administraties/1", json=updated
    )
    item = client.administraties.update(1, naam="Gewijzigd BV")
    assert item.naam == "Gewijzigd BV"


def test_delete(mocked_responses, client):
    mocked_responses.add(
        responses.DELETE, f"{BASE_URL}/api/administraties/1", status=204
    )
    client.administraties.delete(1)  # should not raise


def test_list_filters(mocked_responses, client):
    other = {**ADMINISTRATIE, "id": 2, "naam": "Other BV"}
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE, other]
    )
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE, other]
    )
    by_name = client.administraties.list(name="Test BV")
    assert len(by_name) == 1
    assert by_name[0].id == 1

    by_id = client.administraties.list(id=2)
    assert len(by_id) == 1
    assert by_id[0].naam == "Other BV"


def test_list_filters_not_found(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    assert client.administraties.list(name="Nonexistent") == []


def test_administratie_scope_by_id(client):
    """Positional and keyword ID still work without an HTTP call."""
    scope = client.administratie(1)
    assert scope.admin_id == 1

    scope = client.administratie(id=1)
    assert scope.admin_id == 1


def test_administratie_scope_by_name(mocked_responses, client):
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    scope = client.administratie(name="Test BV")
    assert scope.admin_id == 1


def test_administratie_scope_by_name_auto_paginates(mocked_responses, client):
    first_page = [
        {**ADMINISTRATIE, "id": i + 1, "naam": f"Admin {i + 1}"} for i in range(1000)
    ]
    target = {**ADMINISTRATIE, "id": 1001, "naam": "Target BV"}
    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=first_page
    )
    mocked_responses.add(responses.GET, f"{BASE_URL}/api/administraties", json=[target])

    scope = client.administratie(name="Target BV")

    assert scope.admin_id == 1001
    admin_calls = [
        c
        for c in mocked_responses.calls
        if c.request.url.startswith(f"{BASE_URL}/api/administraties")
    ]
    assert len(admin_calls) == 2
    assert "offset=1000" in admin_calls[1].request.url


def test_administratie_scope_by_name_not_found(mocked_responses, client):
    from mboek._exceptions import NotFoundError

    mocked_responses.add(
        responses.GET, f"{BASE_URL}/api/administraties", json=[ADMINISTRATIE]
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.administratie(name="Nonexistent BV")
    assert "Nonexistent BV" in str(exc_info.value)


def test_administratie_scope_by_name_requires_single_match(mocked_responses, client):
    duplicate = {**ADMINISTRATIE, "id": 2}
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/administraties",
        json=[ADMINISTRATIE, duplicate],
    )
    with pytest.raises(ValueError, match="Test BV"):
        client.administratie(name="Test BV")


def test_administratie_scope_missing_args(client):
    with pytest.raises(ValueError):
        client.administratie()


def test_administratie_scope_ambiguous_args(client):
    with pytest.raises(ValueError):
        client.administratie(1, name="Test BV")
