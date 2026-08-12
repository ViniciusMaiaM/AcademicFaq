import time
from datetime import datetime

import streamlit as st
from services.api import call_api
from services.feedback import submit_feedback


def _render_message(message: dict, index: int):
    """Renderiza uma mensagem da conversa (user/assistant)."""
    role = message.get("role", "user")
    content = message.get("content", "")
    sources = message.get("sources", [])
    cached = message.get("cached", False)
    response_time = message.get("response_time_ms")

    with st.chat_message(role):
        content_col, badge_col = st.columns([4, 1])
        with content_col:
            st.markdown(content)

        if role == "assistant":
            with badge_col:
                if cached:
                    st.markdown(
                        '<span class="cached-badge">📦 Cache</span>', unsafe_allow_html=True
                    )
                if response_time:
                    st.markdown(
                        f'<div class="response-time">⏱️ {response_time:.0f}ms</div>',
                        unsafe_allow_html=True,
                    )

        if role == "assistant" and sources:
            with st.expander("📚 Fontes Consultadas", expanded=False):
                for src in sources:
                    source_title = src.get("source", "Fonte")
                    snippet = src.get("snippet", "")
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <strong>📄 {source_title}</strong><br>
                            <em>{snippet}</em>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

        if role == "assistant" and "feedback_submitted" not in message:
            col1, col2, _ = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"positive_{index}", use_container_width=True):
                    res = submit_feedback(
                        message.get("original_question", ""), message.get("content", ""), "positive"
                    )
                    if res is not None:
                        st.session_state.messages[index]["feedback_submitted"] = "positive"
                        st.success("Obrigado pelo feedback positivo!")
                        time.sleep(0.6)
                        st.rerun()
            with col2:
                if st.button("👎", key=f"negative_{index}", use_container_width=True):
                    res = submit_feedback(
                        message.get("original_question", ""), message.get("content", ""), "negative"
                    )
                    if res is not None:
                        st.session_state.messages[index]["feedback_submitted"] = "negative"
                        st.warning("Feedback registrado. Obrigado!")
                        time.sleep(0.6)
                        st.rerun()
        elif role == "assistant" and "feedback_submitted" in message:
            feedback_icon = "👍" if message["feedback_submitted"] == "positive" else "👎"
            st.caption(f"Feedback enviado: {feedback_icon}")


def _add_assistant_message(result: dict, prompt: str):
    """Adiciona a resposta do assistente ao session_state.messages."""
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "sources": result.get("sources", []),
            "cached": result.get("cached", False),
            "response_time_ms": result.get("response_time_ms"),
            "original_question": prompt,
        }
    )


def render_chat():
    """Renderiza a área principal do chat e processa o input do usuário."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(datetime.now().timestamp())
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

    chat_container = st.container()

    prompt_from_sidebar = (
        st.session_state.pop("selected_question", None)
        if "selected_question" in st.session_state
        else None
    )

    if not st.session_state.conversation_started and not st.session_state.messages:
        st.info(
            "👋 Olá! Sou seu assistente acadêmico com sistema de cache inteligente. Respostas frequentes são servidas instantaneamente!"
        )

    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            _render_message(message, i)

    if prompt_from_sidebar:
        prompt = prompt_from_sidebar
    else:
        prompt = st.chat_input("Digite sua pergunta sobre a universidade...")

    if prompt:
        st.session_state.conversation_started = True
        st.session_state.question_count += 1

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando documentos acadêmicos..."):
                request_data = {
                    "question": prompt,
                    "session_id": st.session_state.session_id,
                    "k": 6,
                }
                result = call_api("/api/v1/ask", method="POST", data=request_data)

                if result:
                    content_col, badge_col = st.columns([4, 1])
                    with content_col:
                        st.markdown(result.get("answer", ""))

                    with badge_col:
                        if result.get("cached", False):
                            st.markdown(
                                '<span class="cached-badge">📦 Cache</span>', unsafe_allow_html=True
                            )
                        if result.get("response_time_ms"):
                            st.markdown(
                                f'<div class="response-time">⏱️ {result["response_time_ms"]:.0f}ms</div>',
                                unsafe_allow_html=True,
                            )

                    if result.get("sources"):
                        with st.expander("📚 Fontes Consultadas", expanded=False):
                            for src in result["sources"]:
                                st.markdown(
                                    f"""
                                <div class="source-card">
                                    <strong>📄 {src.get("source", "")}</strong><br>
                                    <em>{src.get("snippet", "")}</em>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                    _add_assistant_message(result, prompt)
                    st.rerun()
                else:
                    st.error("❌ Erro ao processar sua pergunta. Verifique se a API está rodando.")
