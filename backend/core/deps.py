"""Dependências de FastAPI compartilhadas entre routers — hoje só a de
autenticação, mas é o lugar natural pra outras no futuro.
"""

from fastapi import Depends, Header, HTTPException, status
from models.user import User
from repositories.user import user_rp
from sqlalchemy.orm import Session

from core.database import get_db


def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Autentica a requisição pela API key no header `X-API-Key`.

    Usada como `Depends(get_current_user)` em toda rota que deve exigir
    login (hoje, todas as rotas de negócio — `/ask`, `/cache`, `/feedback`,
    `/metrics` — ficam de fora só `/auth/*` e a raiz `/`).
    """
    user = user_rp.get_by_api_key(db, x_api_key)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")
    return user
