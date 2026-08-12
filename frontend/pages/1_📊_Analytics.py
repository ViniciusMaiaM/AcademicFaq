import pandas as pd
import plotly.express as px
import streamlit as st
from components.auth import render_auth_gate
from services.api import call_api
from utils.session import init_session_state

# Paleta categórica validada (skill dataviz): ordem fixa, não gerada.
SLOT_BLUE = "#2a78d6"
SLOT_ORANGE = "#eb6834"
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"

st.set_page_config(page_title="Analytics - FAQ Acadêmico", page_icon="📊", layout="wide")
init_session_state(st)

if not render_auth_gate():
    st.stop()

st.title("📊 Analytics")
st.caption("Uso, cache e feedback do FAQ Acadêmico")

metrics = call_api("/api/v1/metrics/")
cache_stats = call_api("/api/v1/cache/stats")

if not metrics or not cache_stats:
    st.error("Não foi possível carregar as métricas.")
    st.stop()

# % dos acessos ao cache que foram reaproveitamentos, não a escrita inicial
# (access_count nasce em 1 e só sobe a cada hit). Base é total_accesses, não
# total_questions — essa segunda base pode estourar 100%.
total_accesses = cache_stats["total_accesses"]
reuse_rate = ((total_accesses - cache_stats["cache_size"]) / max(total_accesses, 1)) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Perguntas distintas", metrics["total_questions"])
col2.metric("Satisfação", f"{metrics['satisfaction_rate']:.0f}%")
col3.metric("Itens em cache", cache_stats["cache_size"])
col4.metric("Taxa de reaproveitamento do cache", f"{reuse_rate:.0f}%")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Feedback")
    positive = metrics["positive_feedback"]
    negative = metrics["negative_feedback"]
    if positive + negative > 0:
        df_feedback = pd.DataFrame(
            {"Tipo": ["👍 Positivo", "👎 Negativo"], "Quantidade": [positive, negative]}
        )
        fig = px.bar(
            df_feedback,
            x="Quantidade",
            y="Tipo",
            orientation="h",
            color="Tipo",
            color_discrete_map={"👍 Positivo": STATUS_GOOD, "👎 Negativo": STATUS_CRITICAL},
        )
        fig.update_traces(marker_line_width=0)
        fig.update_layout(showlegend=False, yaxis_title=None, xaxis_title=None, bargap=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum feedback registrado ainda.")

with col_b:
    st.subheader("Cache")
    df_cache = pd.DataFrame(
        {
            "Categoria": ["Reaproveitadas", "Geradas pela 1ª vez"],
            "Quantidade": [
                max(0, total_accesses - cache_stats["cache_size"]),
                cache_stats["cache_size"],
            ],
        }
    )
    fig = px.bar(
        df_cache,
        x="Categoria",
        y="Quantidade",
        color="Categoria",
        color_discrete_sequence=[SLOT_BLUE, SLOT_ORANGE],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=False, xaxis_title=None, bargap=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Perguntas mais frequentes")
if metrics["popular_questions"]:
    df_popular = pd.DataFrame(metrics["popular_questions"]).head(10)
    fig = px.bar(
        df_popular,
        x="count",
        y="question",
        orientation="h",
        color_discrete_sequence=[SLOT_BLUE],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        yaxis_title=None,
        xaxis_title="Frequência",
        height=400,
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma pergunta registrada ainda.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Feedback recente")
    if metrics["recent_feedback"]:
        df_recent = pd.DataFrame(metrics["recent_feedback"])
        df_recent["Tipo"] = df_recent["feedback_type"].map({"positive": "👍", "negative": "👎"})
        st.dataframe(
            df_recent[["Tipo", "question", "created_at"]].rename(
                columns={"question": "Pergunta", "created_at": "Data"}
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum feedback recente.")

with col_d:
    st.subheader("Mais acessadas no cache")
    if cache_stats["most_accessed"]:
        df_cache_top = pd.DataFrame(cache_stats["most_accessed"])
        st.dataframe(
            df_cache_top[["question", "access_count", "last_accessed"]].rename(
                columns={
                    "question": "Pergunta",
                    "access_count": "Acessos",
                    "last_accessed": "Último acesso",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum item em cache ainda.")

if st.button("🔄 Atualizar"):
    st.rerun()
