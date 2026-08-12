from core.security import is_ufrn_email
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_ufrn_domain(cls, v: str) -> str:
        if not is_ufrn_email(v):
            raise ValueError(
                "cadastro permitido apenas com e-mail institucional (domínio deve conter 'ufrn')"
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    email: str
    api_key: str
