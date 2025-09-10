import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# Pasta com documentos
DOCS_PATH = "./documentos"
DB_PATH = "chroma_db"

def load_documents():
    docs = []
    for file in os.listdir(DOCS_PATH):
        print(f"Carregando {file}")
        path = os.path.join(DOCS_PATH, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        else:
            loader = UnstructuredFileLoader(path)
        docs.extend(loader.load())
    return docs

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def create_embeddings():
    # Modelo de embeddings do OpenAI (mais preciso e eficiente)
    return OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small"
    )

def main():
    print("Carregando documentos...")
    docs = load_documents()
    print(f"{len(docs)} documentos carregados.")

    print("Dividindo em chunks...")
    chunks = split_documents(docs)
    print(f"{len(chunks)} chunks gerados.")

    print("Criando embeddings e salvando no ChromaDB...")
    embeddings = create_embeddings()
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=DB_PATH)
    print("Ingestão concluída! Base de conhecimento pronta.")

if __name__ == "__main__":
    main()
