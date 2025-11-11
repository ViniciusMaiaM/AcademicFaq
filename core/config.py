from typing import ClassVar, List, Literal, Optional, Union

from pydantic import Field, HttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    
    # Configuração do banco de dados
    DB_ENGINE: Literal["sqlite", "postgresql"] = Field(default="sqlite")
    DB_USER: Optional[str] = Field(default=None)
    DB_PASSWORD: Optional[str] = Field(default=None)
    DB_HOST: Optional[str] = Field(default=None)
    DB_PORT: Optional[str] = Field(default=None)
    DB_NAME: Optional[str] = Field(default=None)
    
    # URL direta (sobrescreve os campos acima se especificada)
    DATABASE_URL: Optional[str] = Field(default=None)

    # Segurança
    SECRET_KEY: str = Field(default="your-secret-key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    ALLOW_ORIGINS: List[Union[HttpUrl, str]] =Field(default=["*"])
    ALLOW_CREDENTIALS: bool =Field(default=True)
    ALLOW_METHODS: List[str] =Field(default=["*"])
    ALLOW_HEADERS: List[str] =Field(default=["*"])
    CORS_CONFIG: ClassVar[dict] = {
        "allow_origins": ALLOW_ORIGINS,
        "allow_credentials": ALLOW_CREDENTIALS,
        "allow_methods": ALLOW_METHODS,
        "allow_headers": ALLOW_HEADERS,
    }

    # Informações do Projeto
    PROJECT_NAME: str = Field(default="Academic FAQ RAG API")
    PROJECT_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)


    class Config:
        env_file = ".env"
        case_sensitive = True


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if v:
            return v

        data = info.data
        engine = data.get("DB_ENGINE")

        if engine == "postgresql":
            return PostgresDsn.build(
                scheme=engine,
                username=data.get("DB_USER"),
                password=data.get("DB_PASSWORD"),
                host=data.get("DB_HOST"),
                port=data.get("DB_PORT", "5432"),
                path=data.get("DB_NAME") or "",
            )

        
        return "sqlite:///analytics.db" 


settings = Settings()