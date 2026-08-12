"""Cache semântico: reaproveita a resposta de uma pergunta já respondida
quando uma nova pergunta é semanticamente muito parecida, mesmo que o texto
não bata exatamente com nenhuma entrada do cache por hash (`services/hash.py`
já cobre variações triviais de digitação — isto aqui cobre paráfrases reais,
ex. "quando começam as aulas" vs "qual a data de início do período letivo").

Implementado com uma coleção Chroma dedicada (`semantic_cache`), separada da
coleção de chunks dos documentos usada por `services/rag.py` — indexar aqui
só o TEXTO DA PERGUNTA, associado ao `question_hash` correspondente na tabela
SQL `cache` (fonte da verdade da resposta em si).

Risco central: um falso positivo aqui serve a resposta ERRADA com confiança
total, sem nenhum guardrail (item 9) rodando de novo — por isso o
threshold de similaridade (`settings.SEMANTIC_CACHE_MIN_SIMILARITY`) é alto
por padrão e todas as falhas aqui são fail-open (silenciosamente tratadas
como "sem match", nunca derrubam a requisição).
"""

import logging

from core.config import settings
from langchain_community.vectorstores import Chroma

from services.rag import CHROMA_PATH, get_embeddings

logger = logging.getLogger(__name__)

_cache_vectorstore: Chroma | None = None


def get_semantic_cache_vectorstore() -> Chroma:
    """Retorna a coleção Chroma usada para indexar perguntas já respondidas."""
    global _cache_vectorstore
    if _cache_vectorstore is None:
        _cache_vectorstore = Chroma(
            collection_name="semantic_cache",
            persist_directory=CHROMA_PATH,
            embedding_function=get_embeddings(),
        )
    return _cache_vectorstore


def find_semantic_match(question: str) -> str | None:
    """Procura uma pergunta já cacheada semanticamente equivalente.

    Returns:
        O `question_hash` da entrada mais parecida, se a similaridade for
        >= `settings.SEMANTIC_CACHE_MIN_SIMILARITY`; caso contrário `None`.
    """
    if not settings.SEMANTIC_CACHE_ENABLED:
        return None

    try:
        vectorstore = get_semantic_cache_vectorstore()
        results = vectorstore.similarity_search_with_relevance_scores(question, k=1)
    except Exception:
        logger.warning(
            "Falha ao consultar o cache semântico; seguindo sem cache semântico.", exc_info=True
        )
        return None

    if not results:
        return None

    doc, score = results[0]
    if score < settings.SEMANTIC_CACHE_MIN_SIMILARITY:
        return None

    return doc.metadata.get("question_hash")


def index_question(question: str, question_hash: str) -> None:
    """Indexa uma pergunta já respondida para futuras buscas semânticas.

    Usa `question_hash` como id do documento no Chroma: reindexar a mesma
    pergunta (mesmo hash) sobrescreve em vez de duplicar.
    """
    if not settings.SEMANTIC_CACHE_ENABLED:
        return

    try:
        vectorstore = get_semantic_cache_vectorstore()
        vectorstore.add_texts(
            texts=[question],
            metadatas=[{"question_hash": question_hash}],
            ids=[question_hash],
        )
    except Exception:
        logger.warning("Falha ao indexar pergunta no cache semântico.", exc_info=True)
