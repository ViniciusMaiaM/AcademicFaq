import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Analytics Dashboard - FAQ Acadêmico", 
    page_icon="📊", 
    layout="wide"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def call_api(endpoint):
    """Helper function to call API endpoints"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar com a API. Certifique-se de que o servidor está rodando.")
        return None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return None

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }
    .dashboard-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="dashboard-header">
    <h1>📊 Analytics Dashboard</h1>
    <p>Métricas e insights do sistema FAQ Acadêmico</p>
</div>
""", unsafe_allow_html=True)

# Check API connection
api_status = call_api("/")
if not api_status:
    st.stop()

# Get metrics data
metrics = call_api("/metrics")
cache_stats = call_api("/cache/stats")

if not metrics or not cache_stats:
    st.error("Não foi possível carregar os dados de métricas.")
    st.stop()

# Main metrics row
st.header("📈 Métricas Principais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{metrics['total_questions']}</p>
        <p class="metric-label">Total de Perguntas</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{metrics['satisfaction_rate']}%</p>
        <p class="metric-label">Taxa de Satisfação</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{cache_stats['cache_size']}</p>
        <p class="metric-label">Itens em Cache</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    cache_hit_rate = (cache_stats['total_accesses'] / max(metrics['total_questions'], 1)) * 100
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{cache_hit_rate:.1f}%</p>
        <p class="metric-label">Taxa de Cache Hit</p>
    </div>
    """, unsafe_allow_html=True)

# Charts section
st.header("📊 Visualizações")

# Feedback distribution
col1, col2 = st.columns(2)

with col1:
    st.subheader("👍👎 Distribuição de Feedback")
    feedback_data = {
        'Tipo': ['Positivo', 'Negativo'],
        'Quantidade': [metrics['positive_feedback'], metrics['negative_feedback']]
    }
    
    if sum(feedback_data['Quantidade']) > 0:
        fig_feedback = px.pie(
            values=feedback_data['Quantidade'], 
            names=feedback_data['Tipo'],
            color_discrete_sequence=['#28a745', '#dc3545']
        )
        fig_feedback.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_feedback, use_container_width=True)
    else:
        st.info("Nenhum feedback registrado ainda.")

with col2:
    st.subheader("⚡ Performance do Cache")
    cache_data = {
        'Categoria': ['Cache Hits', 'Novas Consultas'],
        'Quantidade': [cache_stats['total_accesses'], max(0, metrics['total_questions'] - cache_stats['total_accesses'])]
    }
    
    fig_cache = px.bar(
        x=cache_data['Categoria'], 
        y=cache_data['Quantidade'],
        color=cache_data['Categoria'],
        color_discrete_sequence=['#17a2b8', '#ffc107']
    )
    fig_cache.update_layout(showlegend=False)
    st.plotly_chart(fig_cache, use_container_width=True)

# Popular questions
st.header("🔥 Perguntas Mais Populares")
if metrics['popular_questions']:
    popular_df = pd.DataFrame(metrics['popular_questions'])
    popular_df = popular_df.head(10)  # Top 10
    
    fig_popular = px.bar(
        popular_df, 
        x='count', 
        y='question',
        orientation='h',
        title="Top 10 Perguntas Mais Frequentes"
    )
    fig_popular.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=500
    )
    st.plotly_chart(fig_popular, use_container_width=True)
    
    # Table view
    st.subheader("📋 Detalhes das Perguntas Populares")
    popular_display = popular_df.copy()
    popular_display['question'] = popular_display['question'].str[:100] + '...'
    popular_display.columns = ['Pergunta', 'Frequência', 'Última Vez']
    st.dataframe(popular_display, use_container_width=True)
else:
    st.info("Nenhuma pergunta registrada ainda.")

# Recent feedback
st.header("💬 Feedback Recente")
if metrics['recent_feedback']:
    feedback_df = pd.DataFrame(metrics['recent_feedback'])
    feedback_df['created_at'] = pd.to_datetime(feedback_df['created_at'])
    feedback_df = feedback_df.sort_values('created_at', ascending=False)
    
    # Display recent feedback
    for _, row in feedback_df.head(5).iterrows():
        feedback_icon = "👍" if row['feedback_type'] == 'positive' else "👎"
        feedback_color = "green" if row['feedback_type'] == 'positive' else "red"
        
        st.markdown(f"""
        <div style="border-left: 4px solid {feedback_color}; padding: 1rem; margin: 0.5rem 0; background-color: #f8f9fa;">
            <strong>{feedback_icon} {row['feedback_type'].title()}</strong><br>
            <em>"{row['question'][:100]}..."</em><br>
            <small>📅 {row['created_at'].strftime('%d/%m/%Y %H:%M')}</small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Nenhum feedback recente.")

# Cache details
st.header("🗄️ Detalhes do Cache")
if cache_stats['most_accessed']:
    st.subheader("🏆 Itens Mais Acessados no Cache")
    cache_df = pd.DataFrame(cache_stats['most_accessed'])
    
    for _, row in cache_df.iterrows():
        st.markdown(f"""
        <div style="border: 1px solid #dee2e6; padding: 1rem; margin: 0.5rem 0; border-radius: 5px;">
            <strong>📄 {row['question'][:100]}...</strong><br>
            <span style="color: #28a745;">✅ {row['access_count']} acessos</span> | 
            <span style="color: #6c757d;">🕒 Último acesso: {row['last_accessed']}</span>
        </div>
        """, unsafe_allow_html=True)

# System health
st.header("🔧 Saúde do Sistema")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="📦 Eficiência do Cache",
        value=f"{cache_hit_rate:.1f}%",
        delta=f"{cache_stats['total_accesses']} hits"
    )

with col2:
    total_feedback = metrics['positive_feedback'] + metrics['negative_feedback']
    st.metric(
        label="💬 Total de Feedback",
        value=total_feedback,
        delta=f"{metrics['positive_feedback']} positivos"
    )

with col3:
    avg_questions_per_session = metrics['total_questions'] / max(1, len(set(metrics.get('sessions', [1]))))
    st.metric(
        label="📊 Perguntas por Sessão",
        value=f"{avg_questions_per_session:.1f}",
        delta="média estimada"
    )

# Refresh button
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.rerun()

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>📊 Analytics Dashboard | Atualizado em tempo real</p>
    <p><small>Dados coletados automaticamente do sistema FAQ Acadêmico</small></p>
</div>
""", unsafe_allow_html=True)
