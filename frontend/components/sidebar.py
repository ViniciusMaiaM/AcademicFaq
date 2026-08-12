import streamlit as st
from services.api import call_api


def render_sidebar():
    st.caption(f"👤 {st.session_state.get('user_email', '')}")
    if st.button("Sair", use_container_width=True):
        st.session_state.api_key = None
        st.session_state.user_email = None
        st.rerun()

    st.divider()
    st.header("📋 Categorias de Perguntas")

    categories = {
        "📅 Calendário Acadêmico": [
            "Quando começam as aulas do primeiro semestre de 2025?",
            "Quais são as datas das férias acadêmicas?",
            "Quando é o período de matrícula?",
            "Quais são os feriados acadêmicos previstos?",
        ],
        "📚 Regulamentos": [
            "Qual é a carga horária mínima para graduação?",
            "Como funciona o sistema de aprovação?",
            "Quais são os critérios para jubilamento?",
            "Como solicitar trancamento de matrícula?",
        ],
        "🎓 TCC e Estágio": [
            "Como funciona o estágio supervisionado?",
            "Quais são os pré-requisitos para o TCC?",
            "Quantas horas de atividades complementares são necessárias?",
            "Qual é o prazo para defesa do TCC?",
        ],
        "👥 Administrativo": [
            "Quem é o vice-reitor?",
            "Como entrar em contato com a coordenação?",
            "Quais são os horários de atendimento?",
            "Como solicitar documentos acadêmicos?",
        ],
    }

    for category, questions in categories.items():
        with st.expander(category):
            for question in questions:
                if st.button(question, key=f"btn_{question}", use_container_width=True):
                    st.session_state.selected_question = question
                    st.rerun()

    st.divider()
    st.header("🔌 Status da API")

    api_status = call_api("/")
    if api_status:
        st.success("✅ API Online")
        st.caption(f"Versão: {api_status.get('version', 'N/A')}")
    else:
        st.error("❌ API Offline")
