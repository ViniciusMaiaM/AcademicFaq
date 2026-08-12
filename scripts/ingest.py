import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredFileLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent

DOCS_PATH = str(REPO_ROOT / "docs")
DB_PATH = str(REPO_ROOT / "chroma_db")


def load_documents():
    docs = []
    for file in os.listdir(DOCS_PATH):
        logger.info("Carregando %s", file)
        path = os.path.join(DOCS_PATH, file)
        if file.endswith(".pdf"):
            loader = PyMuPDFLoader(path)
        else:
            loader = UnstructuredFileLoader(path)
        docs.extend(loader.load())
    return docs


def split_documents(documents):
    # r"\nArt\.\s*\d+" casa só o INÍCIO de um artigo (quebra de linha antes de
    # "Art."), não referências cruzadas no meio de frase (ex.: "conforme o Art. 26").
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[r"\nArt\.\s*\d+", "\n\n", "\n", " ", ""],
        is_separator_regex=True,
        keep_separator="start",
    )
    return splitter.split_documents(documents)


def create_embeddings():
    return OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small"
    )


def reset_collection(embeddings):
    """Remove a coleção existente para que a ingestão seja idempotente."""
    existing = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    existing.delete_collection()


def main():
    logger.info("Carregando documentos...")
    docs = load_documents()
    logger.info("%d documentos carregados.", len(docs))

    logger.info("Dividindo em chunks...")
    chunks = split_documents(docs)
    logger.info("%d chunks gerados.", len(chunks))

    logger.info("Criando embeddings e salvando no ChromaDB...")
    embeddings = create_embeddings()

    logger.info("Limpando coleção existente (se houver) para evitar duplicatas...")
    reset_collection(embeddings)

    Chroma.from_documents(chunks, embeddings, persist_directory=DB_PATH)
    logger.info("Ingestão concluída! Base de conhecimento pronta.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
