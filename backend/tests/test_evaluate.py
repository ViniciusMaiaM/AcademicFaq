"""Testes de scripts/evaluate.py (item 8). Tudo mockado — não depende de
OPENAI_API_KEY válida nem faz chamadas reais ao pipeline de RAG.
"""

import json
from unittest.mock import patch

import pytest

import scripts.evaluate as evaluate


def test_contains_any_keyword_ignores_accent_and_case():
    assert evaluate._contains_any_keyword("O CURSO CONCEDE O GRAU DE BACHARÉL", ["bacharel"])
    assert not evaluate._contains_any_keyword("nada a ver aqui", ["licenciatura"])


def test_load_golden_set_has_expected_shape():
    golden_set = evaluate.load_golden_set()
    assert len(golden_set) > 0
    for item in golden_set:
        assert "id" in item
        assert "category" in item
        assert "question" in item
        assert "expected_keywords" in item


def _fake_answer(question, k=6):
    mapping = {
        "pergunta respondida corretamente": {
            "answer": "As aulas começam em 17/03/2025.",
            "sources": [{"snippet": "Início das aulas 17/03/25"}],
        },
        "pergunta com resposta errada": {
            "answer": "As aulas começam em 01/01/2099.",
            "sources": [{"snippet": "nada relevante aqui"}],
        },
        "pergunta sem relação": {
            "answer": evaluate.FALLBACK_ANSWER,
            "sources": [],
        },
    }
    return mapping[question]


def test_evaluate_item_pass_when_answer_contains_keyword():
    item = {
        "id": "t1",
        "category": "cat",
        "question": "pergunta respondida corretamente",
        "expected_keywords": ["17/03"],
        "expect_fallback": False,
    }
    with patch.object(evaluate, "answer_question", side_effect=_fake_answer):
        result = evaluate.evaluate_item(item)

    assert result["passed"] is True
    assert result["answer_hit"] is True
    assert result["retrieval_hit"] is True
    assert result["fell_back"] is False


def test_evaluate_item_fails_when_answer_missing_keyword():
    item = {
        "id": "t2",
        "category": "cat",
        "question": "pergunta com resposta errada",
        "expected_keywords": ["17/03"],
        "expect_fallback": False,
    }
    with patch.object(evaluate, "answer_question", side_effect=_fake_answer):
        result = evaluate.evaluate_item(item)

    assert result["passed"] is False
    assert result["answer_hit"] is False
    assert result["retrieval_hit"] is False


def test_evaluate_item_negative_control_passes_on_fallback():
    item = {
        "id": "t3",
        "category": "controle_negativo",
        "question": "pergunta sem relação",
        "expected_keywords": [],
        "expect_fallback": True,
    }
    with patch.object(evaluate, "answer_question", side_effect=_fake_answer):
        result = evaluate.evaluate_item(item)

    assert result["passed"] is True
    assert result["fell_back"] is True


def test_evaluate_item_negative_control_fails_when_it_answers():
    item = {
        "id": "t4",
        "category": "controle_negativo",
        "question": "pergunta respondida corretamente",
        "expected_keywords": [],
        "expect_fallback": True,
    }
    with patch.object(evaluate, "answer_question", side_effect=_fake_answer):
        result = evaluate.evaluate_item(item)

    assert result["passed"] is False


def test_summarize_aggregates_metrics_correctly():
    results = [
        {
            "expect_fallback": False,
            "retrieval_hit": True,
            "answer_hit": True,
            "fell_back": False,
            "passed": True,
            "response_time_ms": 100,
        },
        {
            "expect_fallback": False,
            "retrieval_hit": False,
            "answer_hit": False,
            "fell_back": False,
            "passed": False,
            "response_time_ms": 200,
        },
        {
            "expect_fallback": True,
            "retrieval_hit": None,
            "answer_hit": None,
            "fell_back": True,
            "passed": True,
            "response_time_ms": 50,
        },
    ]
    summary = evaluate.summarize(results)

    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["answerable_total"] == 2
    assert summary["retrieval_recall"] == 0.5
    assert summary["answer_recall"] == 0.5
    assert summary["unexpected_fallback_rate"] == 0.0
    assert summary["negative_controls_total"] == 1
    assert summary["negative_controls_passed"] == 1


def test_main_writes_report_and_does_not_crash(tmp_path, monkeypatch):
    fake_golden_set = [
        {
            "id": "t1",
            "category": "cat",
            "question": "pergunta respondida corretamente",
            "expected_keywords": ["17/03"],
            "expect_fallback": False,
        },
        {
            "id": "neg-01",
            "category": "controle_negativo",
            "question": "pergunta sem relação",
            "expected_keywords": [],
            "expect_fallback": True,
        },
    ]
    monkeypatch.setattr(evaluate, "load_golden_set", lambda: fake_golden_set)
    monkeypatch.setattr(evaluate, "RESULTS_DIR", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-for-test")

    with patch.object(evaluate, "answer_question", side_effect=_fake_answer):
        evaluate.main()

    reports = list(tmp_path.glob("*.json"))
    assert len(reports) == 1
    with open(reports[0], encoding="utf-8") as f:
        report = json.load(f)
    assert report["summary"]["total"] == 2
    assert report["summary"]["passed"] == 2
    assert len(report["results"]) == 2


def test_main_exits_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        evaluate.main()
