from unittest.mock import MagicMock

import requests
import services.api as api_service
import streamlit as st


def test_call_api_without_login_sends_no_api_key_header(monkeypatch):
    captured = {}

    def fake_get(url, headers=None):
        captured["headers"] = headers
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"ok": True}
        return resp

    monkeypatch.setattr(api_service.requests, "get", fake_get)

    result = api_service.call_api("/")

    assert result == {"ok": True}
    assert "X-API-Key" not in captured["headers"]


def test_call_api_with_login_sends_api_key_header(monkeypatch):
    st.session_state["api_key"] = "minha-chave-secreta"
    captured = {}

    def fake_get(url, headers=None):
        captured["headers"] = headers
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"ok": True}
        return resp

    monkeypatch.setattr(api_service.requests, "get", fake_get)

    api_service.call_api("/api/v1/cache/stats")

    assert captured["headers"]["X-API-Key"] == "minha-chave-secreta"


def test_call_api_post_sends_json_body_and_headers(monkeypatch):
    st.session_state["api_key"] = "minha-chave-secreta"
    captured = {}

    def fake_post(url, json=None, headers=None):
        captured["json"] = json
        captured["headers"] = headers
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"answer": "42"}
        return resp

    monkeypatch.setattr(api_service.requests, "post", fake_post)

    result = api_service.call_api("/api/v1/ask/", method="POST", data={"question": "?"})

    assert result == {"answer": "42"}
    assert captured["json"] == {"question": "?"}
    assert captured["headers"]["X-API-Key"] == "minha-chave-secreta"


def test_call_api_non_200_returns_none_and_shows_error(monkeypatch):
    resp = MagicMock(status_code=401, text='{"detail":"API key inválida"}')
    monkeypatch.setattr(api_service.requests, "get", lambda url, headers=None: resp)

    error_mock = MagicMock()
    monkeypatch.setattr(api_service.st, "error", error_mock)

    result = api_service.call_api("/api/v1/cache/stats")

    assert result is None
    error_mock.assert_called_once()


def test_call_api_connection_error_returns_none_and_shows_offline_message(monkeypatch):
    def raise_connection_error(url, headers=None):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(api_service.requests, "get", raise_connection_error)

    error_mock = MagicMock()
    monkeypatch.setattr(api_service.st, "error", error_mock)

    result = api_service.call_api("/")

    assert result is None
    error_mock.assert_called_once()
    assert (
        "offline" in error_mock.call_args[0][0].lower() or "Offline" in error_mock.call_args[0][0]
    )
