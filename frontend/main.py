import streamlit as st
from utils.session import init_session_state
from utils.style import load_custom_css
from components.header import render_header
from components.sidebar import render_sidebar
from components.chat import render_chat

st.set_page_config(page_title="FAQ Acadêmico UFRN", page_icon="🎓", layout="wide")
load_custom_css()
init_session_state(st)

render_header()
render_sidebar()
render_chat()
