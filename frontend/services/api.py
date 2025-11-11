import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

def call_api(endpoint, method="GET", data=None):
    """Chama endpoints da API e trata erros genéricos."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ API Offline em http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"Erro ao chamar API: {str(e)}")
        return None
