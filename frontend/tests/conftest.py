import pytest
import streamlit as st


@pytest.fixture(autouse=True)
def reset_session_state():
    # st.session_state é um objeto global no processo fora de `streamlit run`.
    st.session_state.clear()
    yield
    st.session_state.clear()
