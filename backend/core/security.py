"""Utilitários de autenticação: hash de senha, geração de API key e
validação de domínio de e-mail institucional (UFRN).
"""

import secrets

import bcrypt

# bcrypt aceita no máximo 72 bytes de senha.
_BCRYPT_MAX_BYTES = 72


def _encode_for_bcrypt(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return bcrypt.hashpw(_encode_for_bcrypt(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Confere se `password` corresponde ao hash armazenado."""
    return bcrypt.checkpw(_encode_for_bcrypt(password), hashed_password.encode("utf-8"))


def generate_api_key() -> str:
    """Gera uma API key aleatória (256 bits de entropia, URL-safe)."""
    return secrets.token_urlsafe(32)


def is_ufrn_email(email: str) -> bool:
    """Valida se o domínio do e-mail contém 'ufrn' (validação frouxa,
    aceita qualquer subdomínio institucional: ufrn.br, alunos.ufrn.br,
    ceres.ufrn.br, etc. — não valida titularidade real do e-mail).
    """
    if email.count("@") != 1:
        return False
    domain = email.rsplit("@", 1)[1].lower()
    return "ufrn" in domain
