import streamlit as st
from services.auth import login, register


def render_auth_gate() -> bool:
    """Mostra telas de login/cadastro se o usuário ainda não estiver
    autenticado nesta sessão do navegador. Retorna True se já autenticado
    (o app principal pode renderizar); False se ainda não (quem chamar deve
    parar a execução do script, ex. `st.stop()`).
    """
    if st.session_state.get("api_key"):
        return True

    st.title("🎓 FAQ Acadêmico UFRN")
    st.caption("Acesso restrito à comunidade UFRN — cadastre-se com seu e-mail institucional.")

    tab_login, tab_register = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail institucional (@ufrn)", key="login_email")
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            _handle_auth_attempt(login, email, password)

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("E-mail institucional (@ufrn)", key="register_email")
            password = st.text_input(
                "Senha (mínimo 8 caracteres)", type="password", key="register_password"
            )
            submitted = st.form_submit_button("Criar conta", use_container_width=True)

        if submitted:
            _handle_auth_attempt(register, email, password)

    return False


def _handle_auth_attempt(action, email: str, password: str) -> None:
    if not email or not password:
        st.error("Preencha e-mail e senha.")
        return

    ok, body = action(email, password)
    if ok:
        st.session_state.api_key = body["api_key"]
        st.session_state.user_email = body["email"]
        st.rerun()
    else:
        st.error(body["detail"])
