"""Tests for the authentication resource."""

from __future__ import annotations

import pytest
import responses

from mboek import MboekClient
from mboek._exceptions import AuthError, RateLimitError, ValidationError
from tests.conftest import BASE_URL

LOGIN_PAYLOAD = {
    "token": "my-jwt-token",
    "gebruikersnaam": "admin",
    "expires_at": 9999999999,
}


def test_login_success(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    client = MboekClient(BASE_URL)
    result = client.login("admin", "secret")

    assert result.token == "my-jwt-token"
    assert result.gebruikersnaam == "admin"
    assert client.token == "my-jwt-token"


def test_login_in_constructor(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    client = MboekClient(BASE_URL, "admin", "secret")
    assert client.token == "my-jwt-token"


def test_login_invalid_credentials(mocked_responses):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/auth/login",
        json={"error": "Invalid"},
        status=401,
    )
    client = MboekClient(BASE_URL)
    with pytest.raises(AuthError) as exc_info:
        client.login("bad", "creds")
    assert exc_info.value.status_code == 401


def test_login_rate_limited(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json={}, status=429
    )
    client = MboekClient(BASE_URL)
    with pytest.raises(RateLimitError) as exc_info:
        client.login("admin", "pw")
    assert exc_info.value.status_code == 429


def test_login_validation_error(mocked_responses):
    mocked_responses.add(
        responses.POST,
        f"{BASE_URL}/api/auth/login",
        json={"error": "Validation error"},
        status=422,
    )
    client = MboekClient(BASE_URL)
    with pytest.raises(ValidationError) as exc_info:
        client.login("", "")
    assert exc_info.value.status_code == 422


def test_me(mocked_responses, client):
    mocked_responses.add(
        responses.GET,
        f"{BASE_URL}/api/auth/me",
        json={"gebruikersnaam": "admin", "sub": "1"},
    )
    info = client.auth.me()
    assert info["gebruikersnaam"] == "admin"


def test_logout(mocked_responses, client):
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/logout", status=204)
    client.logout()
    assert client.token is None


def test_context_manager_auto_logout(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/logout", status=204)

    with MboekClient(BASE_URL, "admin", "secret") as c:
        assert c.token == "my-jwt-token"
    assert c.token is None


def test_login_from_env_vars(mocked_responses, monkeypatch):
    monkeypatch.setenv("MBOEK_URL", BASE_URL)
    monkeypatch.setenv("MBOEK_USERNAME", "admin")
    monkeypatch.setenv("MBOEK_PASSWORD", "secret")
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    client = MboekClient()
    assert client.token == "my-jwt-token"
    assert client._base_url == BASE_URL


def test_env_var_url_only(mocked_responses, monkeypatch):
    monkeypatch.setenv("MBOEK_URL", BASE_URL)
    monkeypatch.delenv("MBOEK_USERNAME", raising=False)
    monkeypatch.delenv("MBOEK_PASSWORD", raising=False)
    client = MboekClient()
    # No login attempted — no credentials
    assert client.token is None
    assert client._base_url == BASE_URL


def test_explicit_args_override_env_vars(mocked_responses, monkeypatch):
    monkeypatch.setenv("MBOEK_URL", "http://env-host:9999")
    monkeypatch.setenv("MBOEK_USERNAME", "env-user")
    monkeypatch.setenv("MBOEK_PASSWORD", "env-pass")
    # Explicit base_url and credentials override env vars
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    client = MboekClient(BASE_URL, "admin", "secret")
    assert client._base_url == BASE_URL
    assert client.token == "my-jwt-token"


def test_default_url_without_env_var(monkeypatch):
    monkeypatch.delenv("MBOEK_URL", raising=False)
    monkeypatch.delenv("MBOEK_USERNAME", raising=False)
    monkeypatch.delenv("MBOEK_PASSWORD", raising=False)
    client = MboekClient()
    assert client._base_url == "http://localhost:3000"


def test_partial_env_username_only_no_login(mocked_responses, monkeypatch):
    """Only MBOEK_USERNAME set (no password) → no login attempted."""
    monkeypatch.setenv("MBOEK_URL", BASE_URL)
    monkeypatch.setenv("MBOEK_USERNAME", "admin")
    monkeypatch.delenv("MBOEK_PASSWORD", raising=False)
    client = MboekClient()
    assert client.token is None


def test_partial_env_password_only_no_login(mocked_responses, monkeypatch):
    """Only MBOEK_PASSWORD set (no username) → no login attempted."""
    monkeypatch.setenv("MBOEK_URL", BASE_URL)
    monkeypatch.delenv("MBOEK_USERNAME", raising=False)
    monkeypatch.setenv("MBOEK_PASSWORD", "secret")
    client = MboekClient()
    assert client.token is None


def test_no_credentials_no_login(monkeypatch):
    """No env vars and no args → no login, token stays None."""
    monkeypatch.delenv("MBOEK_URL", raising=False)
    monkeypatch.delenv("MBOEK_USERNAME", raising=False)
    monkeypatch.delenv("MBOEK_PASSWORD", raising=False)
    client = MboekClient()
    assert client.token is None


def test_explicit_credentials_override_env_body(mocked_responses, monkeypatch):
    """Explicit credentials are used even when env vars have different values."""
    import json as _json

    monkeypatch.setenv("MBOEK_URL", "http://env-host:9999")
    monkeypatch.setenv("MBOEK_USERNAME", "env-user")
    monkeypatch.setenv("MBOEK_PASSWORD", "env-pass")
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD
    )
    client = MboekClient(BASE_URL, "admin", "secret")
    assert client._base_url == BASE_URL
    assert client.token == "my-jwt-token"
    body = _json.loads(mocked_responses.calls[-1].request.body)
    assert body["gebruikersnaam"] == "admin"
