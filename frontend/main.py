import streamlit as st
from components.auth import render_auth_gate
from components.chat import render_chat
from components.header import render_header
from components.sidebar import render_sidebar
from utils.session import init_session_state
from utils.style import load_custom_css

st.set_page_config(page_title="FAQ Acadêmico UFRN", page_icon="🎓", layout="wide")
load_custom_css()
init_session_state(st)

if not render_auth_gate():
    st.stop()

render_header()
render_sidebar()
render_chat()
