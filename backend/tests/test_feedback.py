from repositories.cache import cache_rp
from services.hash import get_question_hash


def test_positive_feedback_upserts_into_cache(client, auth_headers, db_session):
    payload = {
        "question": "Quando começam as aulas?",
        "answer": "17/03/2025.",
        "feedback_type": "positive",
    }
    resp = client.post("/api/v1/feedback/", json=payload, headers=auth_headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback_type"] == "positive"

    cached = cache_rp.get_by_hash(db_session, get_question_hash(payload["question"]))
    assert cached is not None
    assert cached.answer == "17/03/2025."


def test_negative_feedback_does_not_touch_cache(client, auth_headers, db_session):
    payload = {
        "question": "Pergunta com resposta ruim",
        "answer": "resposta incompleta",
        "feedback_type": "negative",
    }
    resp = client.post("/api/v1/feedback/", json=payload, headers=auth_headers)

    assert resp.status_code == 200, resp.text
    assert resp.json()["feedback_type"] == "negative"

    cached = cache_rp.get_by_hash(db_session, get_question_hash(payload["question"]))
    assert cached is None


def test_feedback_requires_auth(client):
    payload = {"question": "q", "answer": "a", "feedback_type": "positive"}
    resp = client.post("/api/v1/feedback/", json=payload)
    assert resp.status_code == 422, resp.text
