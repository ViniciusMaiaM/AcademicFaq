import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-not-real")

# Registra os models em Base.metadata antes do create_all() de db_session.
import models.cache  # noqa: F401
import models.feedback  # noqa: F401
import models.metric  # noqa: F401
import models.question_frequency  # noqa: F401
import models.user  # noqa: F401
import pytest
from core.database import Base, get_db
from core.rate_limit import limiter
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    # limiter é um singleton com storage em memória, compartilhado entre testes.
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture()
def db_session():
    # StaticPool: sem ele, cada conexão do pool vê um banco ":memory:" diferente.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """TestClient com a app real, mas sem rodar o lifespan (que aqueceria
    vectorstore/LLM/cache semântico de verdade, exigindo uma OPENAI_API_KEY
    válida). Os testes que batem em rotas do RAG mockam
    `answer_question`/`find_semantic_match`/`index_question` diretamente.
    """
    from core.app import start_application

    app = start_application()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    """Cadastra um usuário de teste (e-mail @ufrn) e retorna o header
    `X-API-Key` pronto pra usar em `client.post(..., headers=auth_headers)`
    — toda rota de negócio exige autenticação.
    """
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "teste@alunos.ufrn.br", "password": "senha1234"},
    )
    assert resp.status_code == 201, resp.text
    return {"X-API-Key": resp.json()["api_key"]}
