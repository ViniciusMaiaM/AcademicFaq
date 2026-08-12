import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def call_api(endpoint, method="GET", data=None):
    """Chama endpoints da API e trata erros genéricos.

    Anexa o header `X-API-Key` automaticamente quando o usuário está
    logado (todas as rotas de negócio exigem autenticação, exceto `/` e
    `/api/v1/auth/*` — essas simplesmente ignoram o header se ele vier).
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = {}
        api_key = st.session_state.get("api_key")
        if api_key:
            headers["X-API-Key"] = api_key

        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ API Offline em {API_BASE_URL}")
        return None
    except Exception as e:
        st.error(f"Erro ao chamar API: {str(e)}")
        return None
