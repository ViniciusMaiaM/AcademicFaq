import requests

from services.api import API_BASE_URL


def register(email: str, password: str) -> tuple[bool, dict]:
    """Cadastra um novo usuário. Retorna (sucesso, corpo_da_resposta)."""
    return _post("/api/v1/auth/register", email, password, success_status=201)


def login(email: str, password: str) -> tuple[bool, dict]:
    """Autentica um usuário existente. Retorna (sucesso, corpo_da_resposta)."""
    return _post("/api/v1/auth/login", email, password, success_status=200)


def _post(endpoint: str, email: str, password: str, success_status: int) -> tuple[bool, dict]:
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json={"email": email, "password": password},
        )
    except requests.exceptions.ConnectionError:
        return False, {"detail": f"API offline em {API_BASE_URL}"}
    except Exception as e:
        return False, {"detail": f"Erro ao chamar API: {e}"}

    if response.status_code == success_status:
        return True, response.json()
    return False, {"detail": _extract_error_message(response)}


def _extract_error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text

    detail = body.get("detail", body)
    if isinstance(detail, list):
        return "; ".join(d.get("msg", str(d)) for d in detail)
    return str(detail)
