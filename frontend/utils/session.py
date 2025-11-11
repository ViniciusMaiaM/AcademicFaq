import uuid

def init_session_state(st):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
