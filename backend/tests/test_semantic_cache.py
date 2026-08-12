from unittest.mock import MagicMock

import services.semantic_cache as sc


class FakeDoc:
    def __init__(self, metadata):
        self.metadata = metadata


def test_find_semantic_match_hit_above_threshold(monkeypatch):
    fake_vs = MagicMock()
    fake_vs.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc({"question_hash": "abc123"}), 0.98)
    ]
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    assert sc.find_semantic_match("quando começam as aulas?") == "abc123"


def test_find_semantic_match_below_threshold(monkeypatch):
    fake_vs = MagicMock()
    fake_vs.similarity_search_with_relevance_scores.return_value = [
        (FakeDoc({"question_hash": "abc123"}), 0.5)
    ]
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    assert sc.find_semantic_match("pergunta bem diferente") is None


def test_find_semantic_match_empty_index(monkeypatch):
    fake_vs = MagicMock()
    fake_vs.similarity_search_with_relevance_scores.return_value = []
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    assert sc.find_semantic_match("primeira pergunta de todas") is None


def test_find_semantic_match_disabled_by_config(monkeypatch):
    monkeypatch.setattr(sc.settings, "SEMANTIC_CACHE_ENABLED", False)
    fake_vs = MagicMock()
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    assert sc.find_semantic_match("qualquer pergunta") is None
    fake_vs.similarity_search_with_relevance_scores.assert_not_called()


def test_find_semantic_match_fails_open_on_error(monkeypatch):
    fake_vs = MagicMock()
    fake_vs.similarity_search_with_relevance_scores.side_effect = RuntimeError(
        "chroma indisponível"
    )
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    assert sc.find_semantic_match("qualquer pergunta") is None


def test_index_question_calls_add_texts_with_hash_as_id(monkeypatch):
    fake_vs = MagicMock()
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    sc.index_question("Quando começam as aulas?", "hash-xyz")

    fake_vs.add_texts.assert_called_once_with(
        texts=["Quando começam as aulas?"],
        metadatas=[{"question_hash": "hash-xyz"}],
        ids=["hash-xyz"],
    )


def test_index_question_fails_open_on_error(monkeypatch):
    fake_vs = MagicMock()
    fake_vs.add_texts.side_effect = RuntimeError("falha de rede")
    monkeypatch.setattr(sc, "get_semantic_cache_vectorstore", lambda: fake_vs)

    sc.index_question("pergunta qualquer", "hash-1")  # não deve levantar
