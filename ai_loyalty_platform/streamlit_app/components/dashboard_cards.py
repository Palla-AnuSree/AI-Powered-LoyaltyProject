import streamlit as st

def metric_card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)
