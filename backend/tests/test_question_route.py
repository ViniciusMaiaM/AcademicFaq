from unittest.mock import MagicMock

import api.routes.question as question_route
from services.hash import get_question_hash


def test_full_miss_calls_rag_and_indexes_semantic_cache(client, auth_headers, monkeypatch):
    fake_answer = {
        "question": "Quando começam as aulas?",
        "answer": "As aulas começam em 17/03/2025.",
        "sources": [
            {"source": "calendario.pdf", "snippet": "trecho", "page": "1", "relevance_score": "1"}
        ],
        "total_sources": 1,
    }
    mock_answer = MagicMock(return_value=fake_answer)
    mock_find = MagicMock(return_value=None)
    mock_index = MagicMock()
    monkeypatch.setattr(question_route, "answer_question", mock_answer)
    monkeypatch.setattr(question_route, "find_semantic_match", mock_find)
    monkeypatch.setattr(question_route, "index_question", mock_index)

    resp = client.post(
        "/api/v1/ask/", json={"question": "Quando começam as aulas?"}, headers=auth_headers
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cached"] is False
    assert body["answer"] == "As aulas começam em 17/03/2025."
    mock_answer.assert_called_once()
    mock_find.assert_called_once()
    mock_index.assert_called_once()


def test_ask_without_api_key_is_rejected(client):
    resp = client.post("/api/v1/ask/", json={"question": "Quando começam as aulas?"})
    assert resp.status_code == 422, resp.text


def test_ask_with_invalid_api_key_is_rejected(client):
    resp = client.post(
        "/api/v1/ask/",
        json={"question": "Quando começam as aulas?"},
        headers={"X-API-Key": "chave-que-nao-existe"},
    )
    assert resp.status_code == 401, resp.text


def test_error_result_is_not_indexed_in_semantic_cache(client, auth_headers, monkeypatch):
    error_answer = {
        "question": "pergunta que deu erro",
        "answer": "Sinto muito, ocorreu um erro interno ao processar sua solicitação. Por favor, tente novamente.",
        "sources": [],
        "error": "timeout simulado",
    }
    mock_index = MagicMock()
    monkeypatch.setattr(question_route, "answer_question", lambda q, k: error_answer)
    monkeypatch.setattr(question_route, "find_semantic_match", lambda q: None)
    monkeypatch.setattr(question_route, "index_question", mock_index)

    resp = client.post(
        "/api/v1/ask/", json={"question": "pergunta que deu erro"}, headers=auth_headers
    )

    assert resp.status_code == 200, resp.text
    mock_index.assert_not_called()


def test_semantic_hit_backfills_exact_hash_and_skips_rag(client, auth_headers, monkeypatch):
    fake_answer = {
        "question": "Quando começam as aulas?",
        "answer": "As aulas começam em 17/03/2025.",
        "sources": [
            {"source": "calendario.pdf", "snippet": "trecho", "page": "1", "relevance_score": "1"}
        ],
        "total_sources": 1,
    }
    monkeypatch.setattr(question_route, "answer_question", lambda q, k: fake_answer)
    monkeypatch.setattr(question_route, "find_semantic_match", lambda q: None)
    monkeypatch.setattr(question_route, "index_question", lambda q, h: None)

    resp1 = client.post(
        "/api/v1/ask/", json={"question": "Quando começam as aulas?"}, headers=auth_headers
    )
    assert resp1.json()["cached"] is False

    first_hash = get_question_hash("Quando começam as aulas?")

    mock_answer_2 = MagicMock()
    mock_find_2 = MagicMock(return_value=first_hash)
    mock_index_2 = MagicMock()
    monkeypatch.setattr(question_route, "answer_question", mock_answer_2)
    monkeypatch.setattr(question_route, "find_semantic_match", mock_find_2)
    monkeypatch.setattr(question_route, "index_question", mock_index_2)

    resp2 = client.post(
        "/api/v1/ask/",
        json={"question": "Qual a data de início do período letivo?"},
        headers=auth_headers,
    )

    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert body2["cached"] is True
    assert body2["answer"] == "As aulas começam em 17/03/2025."
    assert body2["question"] == "Qual a data de início do período letivo?"
    mock_answer_2.assert_not_called()
    mock_index_2.assert_called_once()

    # repetir exatamente a mesma frase do hit semântico agora deve ser hit
    # exato (backfill funcionou), sem precisar do cache semântico de novo.
    mock_answer_3 = MagicMock()
    mock_find_3 = MagicMock()
    monkeypatch.setattr(question_route, "answer_question", mock_answer_3)
    monkeypatch.setattr(question_route, "find_semantic_match", mock_find_3)

    resp3 = client.post(
        "/api/v1/ask/",
        json={"question": "Qual a data de início do período letivo?"},
        headers=auth_headers,
    )

    assert resp3.json()["cached"] is True
    assert resp3.json()["answer"] == "As aulas começam em 17/03/2025."
    mock_answer_3.assert_not_called()
    mock_find_3.assert_not_called()
