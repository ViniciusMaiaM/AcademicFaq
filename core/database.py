from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative, sessionmaker

from .config import settings

# engine
if settings.DB_ENGINE == "sqlite":
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )

# sessao como banco de dados
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)



# Modelo base para classes
@as_declarative()
class Base:
    id: Any
    __name__: str

    # Para gerar tabela com o nome da classe
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()



# Gerador de sessões
def get_db() -> Generator:
        
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
  