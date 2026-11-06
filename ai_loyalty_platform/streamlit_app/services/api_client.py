import requests
import streamlit as st
from config import API_BASE_URL, API_V1_PREFIX, REQUEST_TIMEOUT

def api_request(method, path, *, json=None, data=None, authenticated=True):
    url = f"{API_BASE_URL}{API_V1_PREFIX}{path}"
    headers = {}
    token = st.session_state.get("access_token")
    if authenticated and token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, url, json=json, data=data,
                                    headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"Cannot connect to FastAPI at {API_BASE_URL}. Is it running?") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"API error ({response.status_code}): {detail}")
    return response.json() if response.content else None
