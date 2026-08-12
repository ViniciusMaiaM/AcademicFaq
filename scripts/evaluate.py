"""Avalia a qualidade do RAG contra um golden set de perguntas com resposta
conhecida (evals/golden_set.json).

Diferente de um "LLM-as-judge", a checagem aqui é por palavra-chave: cada
pergunta do golden set tem uma lista de `expected_keywords` (fatos reais,
extraídos manualmente dos PDFs em docs/) e o item é considerado acertado se
qualquer uma delas aparece na resposta gerada e/ou nos trechos recuperados.
É uma métrica mais grosseira que uma avaliação semântica, mas é determinística,
não depende de outra chamada de LLM (custo/latência) e já é suficiente para
pegar regressões óbvias — retriever que para de achar a data certa, prompt
que passa a ignorar o contexto, guardrail (item 9) disparando fallback
para perguntas que deveriam ter resposta, etc.

Requer OPENAI_API_KEY válida no .env (chama o pipeline de verdade, sem mocks).

Uso:
    cd backend && python ../scripts/evaluate.py
"""

import json
import os
import sys
import time
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_PATH = REPO_ROOT / "backend"
GOLDEN_SET_PATH = REPO_ROOT / "evals" / "golden_set.json"
RESULTS_DIR = REPO_ROOT / "evals" / "results"

sys.path.insert(0, str(BACKEND_PATH))

from services.rag import FALLBACK_ANSWER, answer_question  # noqa: E402


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower()


def _contains_any_keyword(text: str, keywords: list[str]) -> bool:
    normalized_text = _normalize(text)
    return any(_normalize(keyword) in normalized_text for keyword in keywords)


def load_golden_set() -> list[dict]:
    with open(GOLDEN_SET_PATH, encoding="utf-8") as f:
        return json.load(f)


def evaluate_item(item: dict) -> dict:
    start = time.monotonic()
    result = answer_question(item["question"], k=6)
    elapsed_ms = (time.monotonic() - start) * 1000

    answer = result.get("answer", "")
    sources_text = " ".join(s.get("snippet", "") for s in result.get("sources", []))
    fell_back = answer.strip() == FALLBACK_ANSWER

    expect_fallback = item.get("expect_fallback", False)

    if expect_fallback:
        passed = fell_back
        retrieval_hit = None
        answer_hit = None
    else:
        retrieval_hit = _contains_any_keyword(sources_text, item["expected_keywords"])
        answer_hit = _contains_any_keyword(answer, item["expected_keywords"])
        passed = answer_hit and not fell_back

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "expect_fallback": expect_fallback,
        "fell_back": fell_back,
        "retrieval_hit": retrieval_hit,
        "answer_hit": answer_hit,
        "passed": passed,
        "response_time_ms": round(elapsed_ms, 1),
        "answer_preview": answer[:200],
        "error": result.get("error"),
    }


def summarize(results: list[dict]) -> dict:
    answerable = [r for r in results if not r["expect_fallback"]]
    negative_controls = [r for r in results if r["expect_fallback"]]

    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "answerable_total": len(answerable),
        "retrieval_recall": _rate(answerable, "retrieval_hit"),
        "answer_recall": _rate(answerable, "answer_hit"),
        "unexpected_fallback_rate": _rate(answerable, "fell_back"),
        "negative_controls_total": len(negative_controls),
        "negative_controls_passed": sum(1 for r in negative_controls if r["passed"]),
        "avg_response_time_ms": round(sum(r["response_time_ms"] for r in results) / len(results), 1)
        if results
        else 0,
    }


def _rate(items: list[dict], key: str) -> float:
    if not items:
        return 0.0
    return round(sum(1 for i in items if i[key]) / len(items), 3)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERRO: OPENAI_API_KEY não configurada. Defina no .env antes de rodar a avaliação.")
        sys.exit(1)

    golden_set = load_golden_set()
    print(f"Rodando avaliação com {len(golden_set)} perguntas do golden set...\n")

    results = []
    for item in golden_set:
        result = evaluate_item(item)
        results.append(result)
        status = "OK " if result["passed"] else "FAIL"
        print(
            f"[{status}] {result['id']:12s} ({result['response_time_ms']:>7.1f}ms)  {item['question']}"
        )
        if not result["passed"]:
            print(f"         resposta: {result['answer_preview']!r}")

    summary = summarize(results)
    print("\n--- Resumo ---")
    print(f"Passou: {summary['passed']}/{summary['total']}")
    print(f"Retrieval recall (perguntas respondíveis): {summary['retrieval_recall']:.0%}")
    print(f"Answer recall (perguntas respondíveis):    {summary['answer_recall']:.0%}")
    print(f"Fallback inesperado (deveria ter resposta): {summary['unexpected_fallback_rate']:.0%}")
    print(
        f"Controles negativos corretos: {summary['negative_controls_passed']}/{summary['negative_controls_total']}"
    )
    print(f"Tempo médio de resposta: {summary['avg_response_time_ms']}ms")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / f"{int(time.time())}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\nRelatório salvo em {report_path}")


if __name__ == "__main__":
    main()
