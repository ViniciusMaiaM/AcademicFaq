import streamlit as st

from .api import call_api


def submit_feedback(question, answer, feedback_type):
    """Envia feedback à API."""
    data = {
        "question": question,
        "answer": answer,
        "feedback_type": feedback_type,
        "session_id": st.session_state.session_id
    }
    return call_api("/feedback", method="POST", data=data)
