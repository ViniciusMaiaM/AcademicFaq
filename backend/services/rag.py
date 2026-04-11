"""RAG Chain para Sistema de Consulta Acadêmica.

Este módulo implementa uma cadeia de Retrieval-Augmented Generation (RAG)
para responder perguntas sobre documentos acadêmicos usando OpenAI e ChromaDB.

O sistema permite:
- Carregar documentos de um banco vetorial ChromaDB
- Realizar buscas semânticas com MMR (Maximum Marginal Relevance)
- Gerar respostas detalhadas usando modelos OpenAI GPT
- Fornecer citações e fontes das informações

Autor: Sistema RAG Acadêmico
Versão: 2.0
"""

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os
import re

CHROMA_PATH = "./chroma_db"
load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_vectorstore():
    """Carrega o banco vetorial ChromaDB com embeddings OpenAI.
    
    Esta função inicializa e retorna uma instância do ChromaDB configurada
    com embeddings da OpenAI para realizar buscas semânticas nos documentos.
    
    Returns:
        Chroma: Instância do banco vetorial ChromaDB configurado com embeddings OpenAI.
        
    Raises:
        Exception: Se houver erro na conexão com a API da OpenAI ou no carregamento do banco.
        
    Note:
        - Utiliza o modelo 'text-embedding-3-small' da OpenAI (mais eficiente)
        - Requer OPENAI_API_KEY configurada nas variáveis de ambiente
        - O banco deve estar previamente populado com documentos
    """
    # Configura os embeddings da OpenAI com o modelo mais recente e eficiente
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model="text-embedding-3-small"  # Modelo de embedding mais recente e eficiente
    )
    
    # Retorna instância do ChromaDB com os embeddings configurados
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

def build_qa_chain():
    """Constrói e configura a cadeia de Question-Answering (QA) completa.
    
    Esta função cria uma cadeia RAG completa que combina:
    - Recuperação de documentos relevantes via busca semântica
    - Geração de respostas usando modelo de linguagem OpenAI
    - Template de prompt otimizado para respostas acadêmicas
    
    Returns:
        RetrievalQA: Cadeia de QA configurada e pronta para uso.
        
    Raises:
        Exception: Se houver erro na configuração dos componentes.
        
    Note:
        - Utiliza MMR (Maximum Marginal Relevance) para diversidade nos resultados
        - Configurado para respostas acadêmicas detalhadas em português
        - Temperature baixa (0.1) para consistência nas respostas
    """
    vectorstore = load_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 10,
            "fetch_k": 20,
            "lambda_mult": 0.7
        }
    )

    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.1
    )

    # Template de prompt otimizado para respostas acadêmicas em português
    prompt_template = """
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

Contexto disponível:
{context}

Pergunta do usuário: {question}

Resposta detalhada:
"""

    # Cria o template de prompt com as variáveis necessárias
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template
    )

    # Constrói e retorna a cadeia de QA completa
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",  # Estratégia para combinar documentos
        chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain

def answer_question(question: str, k: int = 6):
    """Responde uma pergunta usando a cadeia RAG configurada.
    
    Esta função é uma interface simplificada que:
    1. Carrega o banco vetorial
    2. Configura o retriever e modelo de linguagem
    3. Executa a busca e geração de resposta
    4. Retorna resposta formatada com fontes
    
    Args:
        question (str): Pergunta a ser respondida.
        k (int, optional): Número de documentos a recuperar. Defaults to 8.
        
    Returns:
        dict: Dicionário contendo:
            - question (str): Pergunta original
            - answer (str): Resposta gerada
            - sources (list): Lista de fontes com snippets
            - total_sources (int): Total de documentos encontrados
            - error (str, optional): Mensagem de erro se houver
            
    Raises:
        Exception: Capturada e retornada como mensagem amigável ao usuário.
        
    Example:
        >>> result = answer_question("Quando é o prazo de matrícula?")
        >>> print(result['answer'])
        >>> print(f"Fontes: {len(result['sources'])}")
    """
    try:
        # Carrega o banco vetorial
        vectorstore = load_vectorstore()
        
        # Configura retriever com parâmetros otimizados
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # MMR para diversidade
            search_kwargs={
                "k": k,  # Número de documentos a recuperar
                "fetch_k": k * 2,  # Busca mais documentos antes de filtrar
                "lambda_mult": 0.7  # Balance relevância/diversidade
            }
        )

        # Configura modelo de linguagem
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.1  # Baixa temperatura para consistência
        )

        # Template de prompt otimizado para respostas acadêmicas detalhadas
        enhanced_prompt_template = """
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

        # Cria o template de prompt com variáveis de entrada
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=enhanced_prompt_template
        )

        # Constrói a cadeia de QA com todos os componentes
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",  # Estratégia de combinação de documentos
            chain_type_kwargs={"prompt": prompt}
        )

        # Executa a consulta e obtém a resposta
        result = qa_chain.invoke({"query": question})
        answer = result["result"]

        # Verifica se a resposta indica que não foi encontrada informação
        # e padroniza a mensagem de erro
        if "não foi possível encontrar" in answer.lower() or "não encontrei" in answer.lower():
            answer = "Sinto muito, não foi possível encontrar o que foi solicitado em nossos arquivos. Por favor, tente reformular sua pergunta ou verifique se a informação está disponível nos documentos carregados."

        # Extrai documentos relevantes para criar lista de fontes
        docs = retriever.get_relevant_documents(question)
        sources = []
        
        # Processa até 4 documentos mais relevantes para incluir como fontes
        for i, doc in enumerate(docs[:4]):
            # Extrai nome do arquivo da fonte
            source_name = doc.metadata.get("source", "Documento desconhecido")
            if "/" in source_name:
                source_name = source_name.split("/")[-1]  # Pega apenas o nome do arquivo
            
            # Cria snippet limpo e formatado do conteúdo
            snippet = re.sub(r"\s+", " ", doc.page_content[:300]).strip()
            page = doc.metadata.get("page", "N/A")
            
            # Adiciona informações da fonte à lista
            sources.append({
                "source": source_name,
                "snippet": snippet,
                "page": str(page),  # Converte para string
                "relevance_score": str(i + 1)  # Converte para string
            })

        # Retorna resposta estruturada com todas as informações
        return {
            "question": question, 
            "answer": answer, 
            "sources": sources,
            "total_sources": len(docs)
        }

    except Exception as e:
        # Trata erros de forma amigável ao usuário
        error_msg = "Sinto muito, ocorreu um erro interno ao processar sua solicitação. Por favor, tente novamente."
        return {
            "question": question, 
            "answer": error_msg, 
            "sources": [],
            "error": str(e)  # Inclui erro técnico para debug
        }


if __name__ == "__main__":
    """Interface de linha de comando para testar o sistema RAG.
    
    Permite interação direta com o sistema através do terminal,
    útil para testes e demonstrações do funcionamento.
    """
    # Constrói a cadeia de QA
    qa = build_qa_chain()
    
    # Loop principal de interação
    while True:
        query = input("\n❓ Pergunta: ")
        
        # Verifica comandos de saída
        if query.lower() in ["sair", "exit", "quit"]:
            print("👋 Até logo!")
            break
            
        # Processa a pergunta e exibe resultado
        result = qa.invoke({"query": query})
        print(f"\n💡 Resposta: {result['result']}")
        
        print(f"\nFontes: {len(result['sources'])} documentos")
        for i, source in enumerate(result['sources']):
            print(f"  {i+1}. {source['source']}: {source['snippet'][:100]}...")
        
