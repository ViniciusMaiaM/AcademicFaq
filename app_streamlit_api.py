import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="FAQ Acadêmico UFRN", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .example-question {
        background-color: #21507e;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        cursor: pointer;
        border-left: 3px solid #1f4e79;
    }
    .example-question:hover {
        background-color: #21507e;
    }
    .source-card {
        background-color: #21507e;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
    }
    .stats-card {
        background-color: #21507e;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .cached-badge {
        background-color: #21507e;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    .response-time {
        color: #666;
        font-size: 0.8rem;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

def call_api(endpoint, method="GET", data=None):
    """Helper function to call API endpoints"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar com a API. Certifique-se de que o servidor está rodando em http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Erro na chamada da API: {str(e)}")
        return None

def submit_feedback(question, answer, feedback_type):
    """Submit feedback to the API"""
    data = {
        "question": question,
        "answer": answer,
        "feedback_type": feedback_type,
        "session_id": st.session_state.session_id
    }
    return call_api("/feedback", method="POST", data=data)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎓 FAQ Acadêmico UFRN</h1>
    <p>Assistente inteligente com cache e analytics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with enhanced features
with st.sidebar:
    st.header("📋 Categorias de Perguntas")
    
    # Example questions by category
    categories = {
        "📅 Calendário Acadêmico": [
            "Quando começam as aulas do primeiro semestre de 2025?",
            "Quais são as datas das férias acadêmicas?",
            "Quando é o período de matrícula?",
            "Quais são os feriados acadêmicos previstos?"
        ],
        "📚 Regulamentos": [
            "Qual é a carga horária mínima para graduação?",
            "Como funciona o sistema de aprovação?",
            "Quais são os critérios para jubilamento?",
            "Como solicitar trancamento de matrícula?"
        ],
        "🎓 TCC e Estágio": [
            "Como funciona o estágio supervisionado?",
            "Quais são os pré-requisitos para o TCC?",
            "Quantas horas de atividades complementares são necessárias?",
            "Qual é o prazo para defesa do TCC?"
        ],
        "👥 Administrativo": [
            "Quem é o vice-reitor?",
            "Como entrar em contato com a coordenação?",
            "Quais são os horários de atendimento?",
            "Como solicitar documentos acadêmicos?"
        ]
    }
    
    for category, questions in categories.items():
        with st.expander(category):
            for question in questions:
                if st.button(question, key=f"btn_{question}", use_container_width=True):
                    st.session_state.selected_question = question
                    st.rerun()
    
    st.divider()
    
    # API Status Check
    st.header("🔌 Status da API")
    api_status = call_api("/")
    if api_status:
        st.success("✅ API Online")
        st.caption(f"Versão: {api_status.get('version', 'N/A')}")
    else:
        st.error("❌ API Offline")
    
    st.divider()
    
    # Live Statistics from API
    st.header("📊 Estatísticas em Tempo Real")
    metrics = call_api("/metrics")
    if metrics:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{metrics['total_questions']}</h3>
                <p>Perguntas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{metrics['satisfaction_rate']}%</h3>
                <p>Satisfação</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Cache stats
        cache_stats = call_api("/cache/stats")
        if cache_stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Cache Hits", cache_stats['total_accesses'])
            with col2:
                st.metric("Itens em Cache", cache_stats['cache_size'])
    
    st.divider()
    
    # Controls
    st.header("⚙️ Controles")
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_started = False
        st.rerun()
    
    if st.button("💾 Exportar Conversa", use_container_width=True):
        if st.session_state.messages:
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "session_id": st.session_state.session_id,
                "messages": st.session_state.messages
            }
            st.download_button(
                label="📥 Baixar JSON",
                data=json.dumps(conversation_data, indent=2, ensure_ascii=False),
                file_name=f"conversa_academica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Main chat interface
chat_container = st.container()

# Handle selected question from sidebar
if hasattr(st.session_state, 'selected_question'):
    prompt = st.session_state.selected_question
    delattr(st.session_state, 'selected_question')
else:
    prompt = None

# Welcome message for new users
if not st.session_state.conversation_started and not st.session_state.messages:
    st.info("👋 Olá! Sou seu assistente acadêmico com sistema de cache inteligente. Respostas frequentes são servidas instantaneamente!")

# Display chat history
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Display message content
            content_col, badge_col = st.columns([4, 1])
            with content_col:
                st.markdown(message["content"])
            
            # Show cache badge and response time for assistant messages
            if message["role"] == "assistant" and "cached" in message:
                with badge_col:
                    if message["cached"]:
                        st.markdown('<span class="cached-badge">📦 Cache</span>', unsafe_allow_html=True)
                    if "response_time_ms" in message:
                        st.markdown(f'<div class="response-time">⏱️ {message["response_time_ms"]:.0f}ms</div>', unsafe_allow_html=True)
            
            # Show sources if it's an assistant message
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Fontes Consultadas", expanded=False):
                    for j, source in enumerate(message["sources"]):
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>📄 {source['source']}</strong><br>
                            <em>{source['snippet']}</em>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Feedback buttons for assistant messages
            if message["role"] == "assistant" and "feedback_submitted" not in message:
                col1, col2, col3 = st.columns([1, 1, 8])
                
                with col1:
                    if st.button("👍", key=f"positive_{i}"):
                        feedback_result = submit_feedback(
                            message.get("original_question", ""), 
                            message["content"], 
                            "positive"
                        )
                        if feedback_result:
                            st.session_state.messages[i]["feedback_submitted"] = "positive"
                            st.success("Obrigado pelo feedback positivo!")
                            time.sleep(1)
                            st.rerun()
                
                with col2:
                    if st.button("👎", key=f"negative_{i}"):
                        feedback_result = submit_feedback(
                            message.get("original_question", ""), 
                            message["content"], 
                            "negative"
                        )
                        if feedback_result:
                            st.session_state.messages[i]["feedback_submitted"] = "negative"
                            st.warning("Feedback registrado. Vamos melhorar!")
                            time.sleep(1)
                            st.rerun()
            
            # Show feedback status if already submitted
            elif message["role"] == "assistant" and "feedback_submitted" in message:
                feedback_icon = "👍" if message["feedback_submitted"] == "positive" else "👎"
                st.caption(f"Feedback enviado: {feedback_icon}")

# Chat input
if not prompt:
    prompt = st.chat_input("Digite sua pergunta sobre a universidade...")

if prompt:
    st.session_state.conversation_started = True
    st.session_state.question_count += 1
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from API
    with st.chat_message("assistant"):
        with st.spinner("🔍 Consultando documentos acadêmicos..."):
            # Call the API
            request_data = {
                "question": prompt,
                "session_id": st.session_state.session_id,
                "k": 6
            }
            
            result = call_api("/ask", method="POST", data=request_data)
            
            if result:
                # Display the answer with performance info
                content_col, badge_col = st.columns([4, 1])
                with content_col:
                    st.markdown(result["answer"])
                
                with badge_col:
                    if result.get("cached", False):
                        st.markdown('<span class="cached-badge">📦 Cache</span>', unsafe_allow_html=True)
                    if result.get("response_time_ms"):
                        st.markdown(f'<div class="response-time">⏱️ {result["response_time_ms"]:.0f}ms</div>', unsafe_allow_html=True)
                
                # Show sources in expander
                if result.get("sources"):
                    with st.expander("📚 Fontes Consultadas", expanded=False):
                        for j, source in enumerate(result["sources"]):
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>📄 {source['source']}</strong><br>
                                <em>{source['snippet']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                    "cached": result.get("cached", False),
                    "response_time_ms": result.get("response_time_ms"),
                    "original_question": prompt
                })
                
                # Auto-scroll to bottom
                st.rerun()
            else:
                st.error("❌ Erro ao processar sua pergunta. Verifique se a API está rodando.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🎓 Sistema RAG com Cache e Analytics | API + Streamlit</p>
</div>
""", unsafe_allow_html=True)
