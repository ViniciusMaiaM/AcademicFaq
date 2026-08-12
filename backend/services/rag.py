"""RAG Chain para Sistema de Consulta Acadêmica.

Implementa uma cadeia de Retrieval-Augmented Generation (RAG) para responder
perguntas sobre documentos acadêmicos usando OpenAI e ChromaDB, com busca
semântica via MMR (Maximum Marginal Relevance).
"""

import logging
import os
import re
from pathlib import Path

from core.config import settings
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

CHROMA_PATH = str(Path(__file__).resolve().parent.parent.parent / "chroma_db")
load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

FALLBACK_ANSWER = (
    "Sinto muito, não foi possível encontrar o que foi solicitado em nossos "
    "arquivos. Por favor, tente reformular sua pergunta ou verifique se a "
    "informação está disponível nos documentos carregados."
)

PROMPT_TEMPLATE = """
Você é um assistente acadêmico especializado que responde perguntas sobre calendário universitário e regulamentos acadêmicos.

INSTRUÇÕES IMPORTANTES:
- Responda SOMENTE com base nos trechos de contexto fornecidos abaixo
- Forneça respostas DETALHADAS e COMPLETAS sempre que possível
- Para perguntas sobre DATAS, procure especificamente por datas no formato DD/MM/AAAA ou por meses específicos
- Inclua TODOS os detalhes relevantes encontrados no contexto
- Explique procedimentos passo a passo quando aplicável
- Se não encontrar informação suficiente no contexto, responda: "Sinto muito, não foi possível encontrar o que foi solicitado em nossos arquivos"
- Seja preciso com datas, prazos e regulamentações
- Cite as fontes específicas (nome do arquivo e seção quando disponível)
- Use linguagem clara, profissional e detalhada em português brasileiro
- Organize a resposta com tópicos e subtópicos quando necessário
- Sempre que possível, forneça contexto adicional e informações relacionadas

Contexto disponível:
{context}

Pergunta do usuário: {question}

Resposta detalhada:
"""

GROUNDEDNESS_PROMPT = """Você é um verificador de qualidade de respostas de um sistema RAG.

CONTEXTO (trechos recuperados dos documentos):
{context}

RESPOSTA GERADA:
{answer}

A RESPOSTA GERADA usa apenas fatos, datas e números presentes no CONTEXTO acima,
sem inventar ou complementar com informação que não está lá? Responda com uma
única palavra: SIM ou NÃO."""


_vectorstore: Chroma | None = None
_llm: ChatOpenAI | None = None
_embeddings: OpenAIEmbeddings | None = None


def get_embeddings() -> OpenAIEmbeddings:
    """Retorna o cliente de embeddings da OpenAI compartilhado entre requisições.

    Extraído de `load_vectorstore()` para que outros consumidores (ex.: o
    cache semântico em `services/semantic_cache.py`) usem exatamente o mesmo
    modelo de embedding do vectorstore principal — vetores gerados por
    modelos diferentes não são comparáveis.
    """
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small"
        )
    return _embeddings


def load_vectorstore() -> Chroma:
    """Carrega o banco vetorial ChromaDB com embeddings OpenAI.

    O vectorstore é caro de inicializar (I/O em disco + client da OpenAI),
    então é construído uma única vez e reutilizado entre requisições.
    """
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embeddings())
    return _vectorstore


def get_llm() -> ChatOpenAI:
    """Retorna o cliente ChatOpenAI compartilhado entre requisições."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.1)
    return _llm


def build_retriever(vectorstore: Chroma, k: int = 6):
    """Cria um retriever MMR balanceando relevância e diversidade dos chunks."""
    return vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": k, "fetch_k": k * 2, "lambda_mult": 0.7}
    )


def has_relevant_context(vectorstore: Chroma, question: str, k: int = 6) -> bool:
    """Verifica se existe pelo menos um chunk realmente relacionado à pergunta.

    Roda ANTES de chamar o LLM: se nada no vectorstore passa do score mínimo
    (`settings.RAG_MIN_RELEVANCE_SCORE`), não faz sentido gastar uma chamada
    ao LLM — ele só teria contexto irrelevante para "responder com base em",
    o que é justamente o cenário que mais convida à alucinação.
    """
    results = vectorstore.similarity_search_with_relevance_scores(question, k=k)
    return any(score >= settings.RAG_MIN_RELEVANCE_SCORE for _, score in results)


def is_grounded(llm: ChatOpenAI, answer: str, docs) -> bool:
    """Verifica, com uma segunda chamada ao LLM, se a resposta gerada está
    de fato fundamentada nos chunks recuperados.

    O prompt principal já instrui o modelo a não inventar, mas isso é só uma
    instrução — nada garantia que fosse seguida. Esta é uma checagem
    independente pós-geração (guardrail contra alucinação).

    Fail-open deliberado: se a própria checagem falhar (erro de rede, rate
    limit, resposta inesperada do LLM), a resposta original é mantida em vez
    de derrubar a requisição inteira por causa de uma checagem de segurança
    que não é o caminho crítico da funcionalidade.
    """
    if not docs:
        return False

    context = "\n\n".join(doc.page_content for doc in docs)

    try:
        check_prompt = GROUNDEDNESS_PROMPT.format(context=context, answer=answer)
        verdict = llm.invoke(check_prompt).content.strip().upper()
        return verdict.startswith("SIM")
    except Exception:
        logger.warning(
            "Falha ao verificar groundedness da resposta; mantendo resposta original.",
            exc_info=True,
        )
        return True


def build_qa_chain(k: int = 6):
    """Constrói a cadeia RetrievalQA (retriever + LLM + prompt).

    Usada tanto pela API (`answer_question`) quanto pela CLI de teste
    no bloco `__main__` — fonte única de configuração do RAG.

    Returns:
        tuple: (RetrievalQA, retriever) — o retriever é retornado à parte
        pois `answer_question` também o usa para montar a lista de fontes.
    """
    vectorstore = load_vectorstore()
    retriever = build_retriever(vectorstore, k)
    llm = get_llm()

    prompt = PromptTemplate(input_variables=["context", "question"], template=PROMPT_TEMPLATE)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff", chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain, retriever


def answer_question(question: str, k: int = 6) -> dict:
    """Responde uma pergunta usando a cadeia RAG configurada.

    Returns:
        dict: question, answer, sources, total_sources e, em caso de
        falha, error.
    """
    try:
        vectorstore = load_vectorstore()

        if not has_relevant_context(vectorstore, question, k):
            return {
                "question": question,
                "answer": FALLBACK_ANSWER,
                "sources": [],
                "total_sources": 0,
            }

        qa_chain, retriever = build_qa_chain(k)

        result = qa_chain.invoke({"query": question})
        answer = result["result"]

        if "não foi possível encontrar" in answer.lower() or "não encontrei" in answer.lower():
            answer = FALLBACK_ANSWER

        docs = retriever.get_relevant_documents(question)

        if answer != FALLBACK_ANSWER and not is_grounded(get_llm(), answer, docs):
            answer = FALLBACK_ANSWER

        sources = []

        for i, doc in enumerate(docs[:4]):
            source_name = doc.metadata.get("source", "Documento desconhecido")
            if "/" in source_name:
                source_name = source_name.split("/")[-1]

            snippet = re.sub(r"\s+", " ", doc.page_content[:300]).strip()
            page = doc.metadata.get("page", "N/A")

            sources.append(
                {
                    "source": source_name,
                    "snippet": snippet,
                    "page": str(page),
                    "relevance_score": str(i + 1),
                }
            )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "total_sources": len(docs),
        }

    except Exception as e:
        error_msg = "Sinto muito, ocorreu um erro interno ao processar sua solicitação. Por favor, tente novamente."
        return {"question": question, "answer": error_msg, "sources": [], "error": str(e)}


if __name__ == "__main__":
    qa, retriever = build_qa_chain()

    while True:
        query = input("\n❓ Pergunta: ")

        if query.lower() in ["sair", "exit", "quit"]:
            print("👋 Até logo!")
            break

        result = qa.invoke({"query": query})
        print(f"\n💡 Resposta: {result['result']}")

        docs = retriever.get_relevant_documents(query)
        print(f"\nFontes: {len(docs)} documentos")
        for i, doc in enumerate(docs):
            snippet = re.sub(r"\s+", " ", doc.page_content[:100]).strip()
            print(f"  {i + 1}. {doc.metadata.get('source', 'desconhecido')}: {snippet}...")
