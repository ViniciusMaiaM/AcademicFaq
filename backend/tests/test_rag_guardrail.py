"""Testes do guardrail contra alucinação (item 9): gate de relevância de
retrieval antes de chamar o LLM, e checagem de groundedness pós-geração.
Tudo mockado — não depende de OPENAI_API_KEY válida nem de rede.
"""

from unittest.mock import MagicMock

import services.rag as rag


class FakeDoc:
    def __init__(self, content, source="regulamento.pdf", page=1):
        self.page_content = content
        self.metadata = {"source": source, "page": page}


def test_has_relevant_context_true_when_score_above_threshold(monkeypatch):
    monkeypatch.setattr(rag.settings, "RAG_MIN_RELEVANCE_SCORE", 0.2)
    vectorstore = MagicMock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc("trecho relevante"), 0.6)
    ]
    assert rag.has_relevant_context(vectorstore, "pergunta") is True


def test_has_relevant_context_false_when_score_below_threshold(monkeypatch):
    monkeypatch.setattr(rag.settings, "RAG_MIN_RELEVANCE_SCORE", 0.5)
    vectorstore = MagicMock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc("trecho pouco relevante"), 0.4)
    ]
    assert rag.has_relevant_context(vectorstore, "pergunta") is False


def test_is_grounded_true_when_llm_confirms():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="SIM")
    assert rag.is_grounded(llm, "resposta qualquer", [FakeDoc("contexto")]) is True


def test_is_grounded_false_when_llm_denies():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="NÃO")
    assert rag.is_grounded(llm, "resposta inventada", [FakeDoc("contexto")]) is False


def test_is_grounded_false_when_no_docs():
    llm = MagicMock()
    assert rag.is_grounded(llm, "resposta qualquer", []) is False
    llm.invoke.assert_not_called()


def test_is_grounded_fails_open_when_llm_check_errors():
    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("timeout simulado")
    assert rag.is_grounded(llm, "resposta qualquer", [FakeDoc("contexto")]) is True


def test_answer_question_skips_llm_when_no_relevant_context(monkeypatch):
    vectorstore = MagicMock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc("trecho irrelevante"), 0.01)
    ]
    monkeypatch.setattr(rag, "load_vectorstore", lambda: vectorstore)
    build_qa_chain_mock = MagicMock()
    monkeypatch.setattr(rag, "build_qa_chain", build_qa_chain_mock)

    result = rag.answer_question("Qual a capital da França?")

    assert result["answer"] == rag.FALLBACK_ANSWER
    assert result["sources"] == []
    assert result["total_sources"] == 0
    build_qa_chain_mock.assert_not_called()


def test_answer_question_replaces_ungrounded_answer_with_fallback(monkeypatch):
    vectorstore = MagicMock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc("As matrículas ocorrem entre 01/03 e 10/03."), 0.8)
    ]
    monkeypatch.setattr(rag, "load_vectorstore", lambda: vectorstore)

    retriever = MagicMock()
    retriever.get_relevant_documents.return_value = [
        FakeDoc("As matrículas ocorrem entre 01/03 e 10/03.")
    ]
    qa_chain = MagicMock()
    qa_chain.invoke.return_value = {"result": "As matrículas ocorrem entre 15/04 e 30/04."}
    monkeypatch.setattr(rag, "build_qa_chain", lambda k: (qa_chain, retriever))

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="NÃO")
    monkeypatch.setattr(rag, "get_llm", lambda: llm)

    result = rag.answer_question("Quando são as matrículas?")

    assert result["answer"] == rag.FALLBACK_ANSWER


def test_answer_question_keeps_grounded_answer(monkeypatch):
    vectorstore = MagicMock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc("As matrículas ocorrem entre 01/03 e 10/03."), 0.8)
    ]
    monkeypatch.setattr(rag, "load_vectorstore", lambda: vectorstore)

    retriever = MagicMock()
    retriever.get_relevant_documents.return_value = [
        FakeDoc("As matrículas ocorrem entre 01/03 e 10/03.")
    ]
    qa_chain = MagicMock()
    qa_chain.invoke.return_value = {"result": "As matrículas ocorrem entre 01/03 e 10/03."}
    monkeypatch.setattr(rag, "build_qa_chain", lambda k: (qa_chain, retriever))

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="SIM")
    monkeypatch.setattr(rag, "get_llm", lambda: llm)

    result = rag.answer_question("Quando são as matrículas?")

    assert result["answer"] == "As matrículas ocorrem entre 01/03 e 10/03."
    assert len(result["sources"]) == 1
