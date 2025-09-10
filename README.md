# FAQ Acadêmico – RAG (Python + LangChain)

Este projeto monta um chatbot acadêmico que responde com base nos documentos oficiais (calendário, regulamento, regimento) usando RAG + OpenAI com sistema de cache e analytics.

## 📋 Pré-requisitos
- Python 3.10+
- Chave da OpenAI (`OPENAI_API_KEY`)

## 🚀 Instalação e Configuração

### 1. Clone o repositório e instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua chave da OpenAI
# Substitua o valor vazio por sua chave real
```

**Importante**: Abra o arquivo `.env` e substitua `OPENAI_API_KEY=` por `OPENAI_API_KEY=sua_chave_aqui`

## 📚 Como Rodar o Projeto

### **PASSO 1: Execute o Ingest (OBRIGATÓRIO)**
⚠️ **IMPORTANTE**: Execute este comando PRIMEIRO para processar os documentos e criar a base de conhecimento:

```bash
python ingest.py
```

Este comando irá:
- Carregar todos os PDFs da pasta `documentos/`
- Dividir os documentos em chunks
- Criar embeddings usando OpenAI
- Salvar tudo no banco vetorial ChromaDB

### **PASSO 2: Inicie a API**
Em um terminal, execute:

```bash
python api_enhanced.py
```

A API estará disponível em: `http://localhost:8000`

### **PASSO 3: Inicie a Interface Streamlit**
Em outro terminal, execute:

```bash
streamlit run app_streamlit_api.py
```

A interface web estará disponível em: `http://localhost:8501`

## 🎯 Funcionalidades

- **Chat Inteligente**: Perguntas e respostas baseadas nos documentos oficiais
- **Sistema de Cache**: Respostas frequentes são servidas instantaneamente
- **Analytics em Tempo Real**: Métricas de uso e satisfação
- **Feedback do Usuário**: Sistema de avaliação com 👍/👎
- **Fontes Transparentes**: Mostra quais documentos foram consultados
- **Categorias Organizadas**: Perguntas pré-definidas por categoria

## 📊 Monitoramento

Acesse `http://localhost:8000/docs` para ver a documentação interativa da API.

## 🔧 Estrutura do Projeto

```
├── documentos/           # PDFs dos regulamentos acadêmicos
├── ingest.py            # Script para processar documentos
├── api_enhanced.py      # API FastAPI com cache e analytics
├── app_streamlit_api.py # Interface web Streamlit
├── rag_chain.py         # Lógica do RAG
├── requirements.txt     # Dependências Python
└── .env                 # Variáveis de ambiente
```

## ❗ Solução de Problemas

- **Erro "API Offline"**: Certifique-se que `python api_enhanced.py` está rodando
- **Respostas vazias**: Execute `python ingest.py` primeiro
- **Erro de API Key**: Verifique se `OPENAI_API_KEY` está no arquivo `.env`

