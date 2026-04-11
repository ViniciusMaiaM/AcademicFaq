import streamlit as st

def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>🎓 FAQ Acadêmico UFRN</h1>
        <p>Assistente inteligente com cache e analytics</p>
    </div>
    """, unsafe_allow_html=True)
