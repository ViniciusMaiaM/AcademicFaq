from unittest.mock import MagicMock

import requests
import services.auth as auth_service


def test_register_success_returns_body(monkeypatch):
    fake_resp = MagicMock(status_code=201)
    fake_resp.json.return_value = {"email": "a@ufrn.br", "api_key": "abc123"}
    monkeypatch.setattr(auth_service.requests, "post", lambda *a, **kw: fake_resp)

    ok, body = auth_service.register("a@ufrn.br", "senha1234")

    assert ok is True
    assert body["api_key"] == "abc123"


def test_login_success_returns_body(monkeypatch):
    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"email": "a@ufrn.br", "api_key": "abc123"}
    monkeypatch.setattr(auth_service.requests, "post", lambda *a, **kw: fake_resp)

    ok, body = auth_service.login("a@ufrn.br", "senha1234")

    assert ok is True
    assert body["api_key"] == "abc123"


def test_register_error_with_string_detail(monkeypatch):
    fake_resp = MagicMock(status_code=409)
    fake_resp.json.return_value = {"detail": "E-mail já cadastrado"}
    monkeypatch.setattr(auth_service.requests, "post", lambda *a, **kw: fake_resp)

    ok, body = auth_service.register("a@ufrn.br", "senha1234")

    assert ok is False
    assert body["detail"] == "E-mail já cadastrado"


def test_register_error_with_pydantic_validation_list(monkeypatch):
    fake_resp = MagicMock(status_code=422)
    fake_resp.json.return_value = {
        "detail": [{"msg": "Value error, cadastro permitido apenas com e-mail institucional"}]
    }
    monkeypatch.setattr(auth_service.requests, "post", lambda *a, **kw: fake_resp)

    ok, body = auth_service.register("a@gmail.com", "senha1234")

    assert ok is False
    assert "institucional" in body["detail"]


def test_login_treats_201_as_failure(monkeypatch):
    fake_resp = MagicMock(status_code=201)
    fake_resp.json.return_value = {"email": "a@ufrn.br", "api_key": "abc123"}
    monkeypatch.setattr(auth_service.requests, "post", lambda *a, **kw: fake_resp)

    ok, _ = auth_service.login("a@ufrn.br", "senha1234")

    assert ok is False


def test_connection_error_does_not_raise(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(auth_service.requests, "post", raise_connection_error)

    ok, body = auth_service.login("a@ufrn.br", "senha1234")

    assert ok is False
    assert "offline" in body["detail"].lower()


def test_unexpected_exception_does_not_raise(monkeypatch):
    def raise_unexpected(*args, **kwargs):
        raise RuntimeError("algo inesperado")

    monkeypatch.setattr(auth_service.requests, "post", raise_unexpected)

    ok, body = auth_service.register("a@ufrn.br", "senha1234")

    assert ok is False
    assert "detail" in body
