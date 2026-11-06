import streamlit as st
from components.access import require_role
from components.chatbot import render_chatbot

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

require_role(
    "customer",
    "outlet_user",
    "support",
    "supervisor",
    "admin"
)

st.title("🤖 AI Loyalty Assistant")

render_chatbot()