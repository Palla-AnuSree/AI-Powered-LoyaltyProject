import streamlit as st
from services.api_client import api_request

def login(email, password):
    # FastAPI OAuth2PasswordRequestForm expects username/password form fields.
    return api_request("POST", "/auth/token",
                       data={"username": email, "password": password},
                       authenticated=False)

def get_current_user():
    return api_request("GET", "/auth/me")

def logout():
    for key in ("access_token", "user", "chat_messages"):
        st.session_state.pop(key, None)
