from core.config import settings
from core.database import get_db
from core.rate_limit import limiter
from core.security import generate_api_key, hash_password, verify_password
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from repositories.user import user_rp
from schemas.auth import AuthResponse, UserCreate, UserLogin
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthController:
    """Cadastro e login com e-mail institucional (@ufrn) — autenticação por
    API key simples (sem sessão/JWT): o login devolve a mesma chave gerada
    no cadastro, que o cliente passa em `X-API-Key` em todas as chamadas
    seguintes.
    """

    @router.post("/register", response_model=AuthResponse, status_code=201)
    @limiter.limit(settings.RATE_LIMIT_AUTH)
    def register(
        request: Request, payload: UserCreate, response: Response, db: Session = Depends(get_db)
    ):
        if user_rp.get_by_email(db, payload.email):
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")

        user = user_rp.create(
            db,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            api_key=generate_api_key(),
        )
        return AuthResponse(email=user.email, api_key=user.api_key)

    @router.post("/login", response_model=AuthResponse)
    @limiter.limit(settings.RATE_LIMIT_AUTH)
    def login(
        request: Request, payload: UserLogin, response: Response, db: Session = Depends(get_db)
    ):
        user = user_rp.get_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

        return AuthResponse(email=user.email, api_key=user.api_key)
