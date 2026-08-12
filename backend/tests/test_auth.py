import pytest
from core.security import generate_api_key, hash_password, is_ufrn_email, verify_password
from pydantic import ValidationError
from schemas.auth import UserCreate


def test_hash_password_and_verify_roundtrip():
    hashed = hash_password("minhasenha123")
    assert verify_password("minhasenha123", hashed)
    assert not verify_password("senhaerrada", hashed)


def test_hash_password_never_stores_plaintext():
    hashed = hash_password("minhasenha123")
    assert "minhasenha123" not in hashed


def test_generate_api_key_is_unique_and_long():
    keys = {generate_api_key() for _ in range(20)}
    assert len(keys) == 20
    assert all(len(k) > 30 for k in keys)


@pytest.mark.parametrize(
    "email,expected",
    [
        ("aluno@ufrn.br", True),
        ("aluno@alunos.ufrn.br", True),
        ("prof@ceres.ufrn.br", True),
        ("ALUNO@UFRN.BR", True),
        ("aluno@gmail.com", False),
        ("ufrn.aluno@gmail.com", False),  # "ufrn" no local-part não conta
        ("sem-arroba", False),
        ("a@b@ufrn.br", False),  # e-mail malformado (dois @)
    ],
)
def test_is_ufrn_email(email, expected):
    assert is_ufrn_email(email) is expected


def test_user_create_schema_rejects_non_ufrn_email():
    with pytest.raises(ValidationError):
        UserCreate(email="aluno@gmail.com", password="senha1234")


def test_user_create_schema_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="aluno@ufrn.br", password="curta")


def test_user_create_schema_accepts_valid_input():
    user = UserCreate(email="aluno@alunos.ufrn.br", password="senha1234")
    assert user.email == "aluno@alunos.ufrn.br"


def test_register_creates_user_and_returns_api_key(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "aluno@alunos.ufrn.br", "password": "senha1234"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "aluno@alunos.ufrn.br"
    assert len(body["api_key"]) > 20


def test_register_rejects_non_ufrn_email(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "aluno@gmail.com", "password": "senha1234"},
    )
    assert resp.status_code == 422, resp.text


def test_register_rejects_duplicate_email(client):
    payload = {"email": "aluno@alunos.ufrn.br", "password": "senha1234"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409, second.text


def test_login_with_correct_credentials_returns_same_api_key(client):
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "aluno@alunos.ufrn.br", "password": "senha1234"},
    )
    api_key = register_resp.json()["api_key"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "aluno@alunos.ufrn.br", "password": "senha1234"},
    )
    assert login_resp.status_code == 200, login_resp.text
    assert login_resp.json()["api_key"] == api_key


def test_login_with_wrong_password_is_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "aluno@alunos.ufrn.br", "password": "senha1234"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "aluno@alunos.ufrn.br", "password": "senhaerrada"},
    )
    assert resp.status_code == 401, resp.text


def test_login_with_unknown_email_is_rejected(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ninguem@alunos.ufrn.br", "password": "senha1234"},
    )
    assert resp.status_code == 401, resp.text


def test_protected_route_without_header_is_rejected(client):
    resp = client.get("/api/v1/cache/stats")
    assert resp.status_code == 422, resp.text


def test_protected_route_with_invalid_key_is_rejected(client):
    resp = client.get("/api/v1/cache/stats", headers={"X-API-Key": "chave-invalida"})
    assert resp.status_code == 401, resp.text


def test_protected_route_with_valid_key_succeeds(client, auth_headers):
    resp = client.get("/api/v1/cache/stats", headers=auth_headers)
    assert resp.status_code == 200, resp.text


def test_root_route_does_not_require_auth(client):
    resp = client.get("/")
    assert resp.status_code == 200
