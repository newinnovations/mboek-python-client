"""Tests for the authentication resource."""

from __future__ import annotations

import responses

from mboek import MboekClient
from mboek._exceptions import AuthError, RateLimitError

BASE_URL = "http://localhost:3000"

LOGIN_PAYLOAD = {
    "token": "my-jwt-token",
    "gebruikersnaam": "admin",
    "expires_at": 9999999999,
}


def test_login_success(mocked_responses):
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD)
    client = MboekClient(BASE_URL)
    result = client.login("admin", "secret")

    assert result.token == "my-jwt-token"
    assert result.gebruikersnaam == "admin"
    assert client.token == "my-jwt-token"


def test_login_in_constructor(mocked_responses):
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD)
    client = MboekClient(BASE_URL, "admin", "secret")
    assert client.token == "my-jwt-token"


def test_login_invalid_credentials(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json={"error": "Invalid"}, status=401
    )
    client = MboekClient(BASE_URL)
    try:
        client.login("bad", "creds")
        assert False, "Expected AuthError"
    except AuthError as e:
        assert e.status_code == 401


def test_login_rate_limited(mocked_responses):
    mocked_responses.add(
        responses.POST, f"{BASE_URL}/api/auth/login", json={}, status=429
    )
    client = MboekClient(BASE_URL)
    try:
        client.login("admin", "pw")
        assert False, "Expected RateLimitError"
    except RateLimitError as e:
        assert e.status_code == 429


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
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD)
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/logout", status=204)

    with MboekClient(BASE_URL, "admin", "secret") as c:
        assert c.token == "my-jwt-token"
    assert c.token is None


def test_login_from_env_vars(mocked_responses, monkeypatch):
    monkeypatch.setenv("MBOEK_URL", BASE_URL)
    monkeypatch.setenv("MBOEK_USERNAME", "admin")
    monkeypatch.setenv("MBOEK_PASSWORD", "secret")
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD)
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
    mocked_responses.add(responses.POST, f"{BASE_URL}/api/auth/login", json=LOGIN_PAYLOAD)
    client = MboekClient(BASE_URL, "admin", "secret")
    assert client._base_url == BASE_URL
    assert client.token == "my-jwt-token"


def test_default_url_without_env_var(monkeypatch):
    monkeypatch.delenv("MBOEK_URL", raising=False)
    monkeypatch.delenv("MBOEK_USERNAME", raising=False)
    monkeypatch.delenv("MBOEK_PASSWORD", raising=False)
    client = MboekClient()
    assert client._base_url == "http://localhost:3000"
