import re
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative, sessionmaker

from .config import settings

if settings.DB_ENGINE == "sqlite":
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        if "__tablename__" in cls.__dict__:
            return cls.__dict__["__tablename__"]

        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    def as_dict(self) -> dict:
        """Serializa as colunas do model num dict plano.

        Usado pelos repositórios (`cache.py`, `metric.py`) pra montar as
        respostas de `/cache/stats` e `/metrics/` — chamavam `.as_dict()`
        desde sempre, mas o método nunca existiu na Base, então as duas
        rotas derrubavam com `AttributeError` sempre que havia pelo menos
        um registro real (com a lista vazia, o list comprehension nunca
        chega a chamar o método, por isso passou despercebido).
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
