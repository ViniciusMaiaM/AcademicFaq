from typing import Literal

from pydantic import Field, HttpUrl, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_ENGINE: Literal["sqlite", "postgresql"] = Field(default="sqlite")
    DB_USER: str | None = Field(default=None)
    DB_PASSWORD: str | None = Field(default=None)
    DB_HOST: str | None = Field(default=None)
    DB_PORT: str | None = Field(default=None)
    DB_NAME: str | None = Field(default=None)

    DATABASE_URL: str | None = Field(default=None)

    SECRET_KEY: str = Field(default="your-secret-key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    ALLOW_ORIGINS: list[HttpUrl | str] = Field(default=["http://localhost:8501"])
    ALLOW_CREDENTIALS: bool = Field(default=False)
    ALLOW_METHODS: list[str] = Field(default=["*"])
    ALLOW_HEADERS: list[str] = Field(default=["*"])

    RATE_LIMIT_ASK: str = Field(default="10/minute")
    RATE_LIMIT_AUTH: str = Field(default="5/minute")

    # 0-1, maior é melhor. Abaixo disso, has_relevant_context() nem chama o LLM.
    RAG_MIN_RELEVANCE_SCORE: float = Field(default=0.2)

    # Calibrado contra o par mais perigoso do domínio (embeddings reais, score do Chroma):
    #   "início" vs "término" de período letivo: 0.72
    #   "início" (mesmo sentido, fraseado diferente): 0.89
    #   "TCC I" vs "estágio" (assuntos diferentes): 0.35
    #   "TCC I" (mesmo sentido, fraseado diferente): 0.84
    # 0.85 fica acima do par perigoso e ainda captura parte das paráfrases legítimas.
    SEMANTIC_CACHE_ENABLED: bool = Field(default=True)
    SEMANTIC_CACHE_MIN_SIMILARITY: float = Field(default=0.85)

    PROJECT_NAME: str = Field(default="Academic FAQ RAG API")
    PROJECT_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Sem isso, chaves do .env que não são campos daqui (OPENAI_API_KEY,
        # OPENAI_MODEL) derrubam a importação com ValidationError.
        extra = "ignore"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info) -> str:
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

    @model_validator(mode="after")
    def validate_cors(self) -> "Settings":
        if self.ALLOW_CREDENTIALS and "*" in self.ALLOW_ORIGINS:
            raise ValueError(
                "ALLOW_ORIGINS não pode conter '*' quando ALLOW_CREDENTIALS=True "
                "(combinação inválida pela especificação CORS). "
                "Defina ALLOW_ORIGINS com origens explícitas no .env."
            )
        return self


settings = Settings()
