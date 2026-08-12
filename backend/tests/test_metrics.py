from repositories.feedback import feedback_rp
from repositories.question_frequency import question_frequency_rp
from schemas.feedback import FeedbackRequest


def test_metrics_empty(client, auth_headers):
    resp = client.get("/api/v1/metrics/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_questions"] == 0
    assert body["popular_questions"] == []
    assert body["recent_feedback"] == []
    assert body["satisfaction_rate"] == 0


def test_metrics_with_real_data(client, auth_headers, db_session):
    question_frequency_rp.increment_frequency(db_session, "hash1", "Quando começam as aulas?")
    question_frequency_rp.increment_frequency(db_session, "hash1", "Quando começam as aulas?")

    feedback_rp.create_feedback(
        db_session,
        FeedbackRequest(question="Q1", answer="A1", feedback_type="positive"),
        "hash1",
    )
    feedback_rp.create_feedback(
        db_session,
        FeedbackRequest(question="Q2", answer="A2", feedback_type="negative"),
        "hash2",
    )

    resp = client.get("/api/v1/metrics/", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_questions"] == 1
    assert body["positive_feedback"] == 1
    assert body["negative_feedback"] == 1
    assert body["satisfaction_rate"] == 50.0
    assert len(body["popular_questions"]) == 1
    assert body["popular_questions"][0]["question"] == "Quando começam as aulas?"
    assert body["popular_questions"][0]["count"] == 2
    assert len(body["recent_feedback"]) == 2


def test_metrics_requires_auth(client):
    assert client.get("/api/v1/metrics/").status_code == 422
