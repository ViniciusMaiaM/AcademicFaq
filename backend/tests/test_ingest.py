"""Testes de scripts/ingest.py.

`load_documents`/`split_documents` rodam de verdade contra os PDFs reais em
docs/ (não precisam de OPENAI_API_KEY — só leem arquivo e fazem chunking).
Pressupõe execução a partir da raiz do repo (mesma convenção do resto do
projeto: `docs/` é relativo ao cwd).

O restante do pipeline (embeddings + Chroma) é mockado — não depende de rede
nem de chave da OpenAI válida.
"""

import re
from unittest.mock import MagicMock

import scripts.ingest as ingest


def test_load_and_split_real_pdfs_no_glued_text_regression():
    docs = ingest.load_documents()
    assert len(docs) > 0

    chunks = ingest.split_documents(docs)
    assert len(chunks) > 0

    # Casa datas coladas sem espaço, ex. "17dedezembrode2024".
    glued_date_pattern = re.compile(r"[a-zà-ú]\d{2}de\w+de\d{4}", re.IGNORECASE)
    glued = [c for c in chunks if glued_date_pattern.search(c.page_content)]
    assert glued == [], f"{len(glued)} chunk(s) com datas coladas (regressão do item 6)"

    assert any("17/03/25" in c.page_content for c in chunks)


def test_ingest_main_is_idempotent(tmp_path, monkeypatch):
    """Item 2: rodar a ingestão duas vezes seguidas não deve duplicar
    embeddings na coleção.
    """
    monkeypatch.setattr(ingest, "DB_PATH", str(tmp_path / "chroma_test"))

    fake_embeddings = MagicMock()
    fake_embeddings.embed_documents.side_effect = lambda texts: [[0.0, 0.0, 0.0] for _ in texts]
    fake_embeddings.embed_query.side_effect = lambda t: [0.0, 0.0, 0.0]
    monkeypatch.setattr(ingest, "create_embeddings", lambda: fake_embeddings)

    ingest.main()
    count_after_first_run = _collection_count(ingest.DB_PATH, fake_embeddings)

    ingest.main()
    count_after_second_run = _collection_count(ingest.DB_PATH, fake_embeddings)

    assert count_after_first_run > 0
    assert count_after_second_run == count_after_first_run


def _collection_count(db_path: str, embeddings) -> int:
    from langchain_community.vectorstores import Chroma

    return Chroma(persist_directory=db_path, embedding_function=embeddings)._collection.count()
