import streamlit as st
from uuid import uuid4

from services.api_client import api_request


def render_chatbot():

    st.subheader("Loyalty Support Assistant")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    # Initialize unique chat session
    if "chat_session_id" not in st.session_state:
        st.session_state["chat_session_id"] = str(uuid4())

    # Display previous messages
    for message in st.session_state["chat_messages"]:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message.get("sources"):
                st.caption("Sources: " + ", ".join(message["sources"]))

    # Get user input
    prompt = st.chat_input("Ask about points, rewards or orders...")

    if prompt:

        st.session_state["chat_messages"].append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                try:
                    result = api_request(
                        "POST",
                        "/chatbot/chat",
                        json={
                            "message": prompt,
                            "session_id": st.session_state["chat_session_id"]
                        }
                    )

                    answer = result.get(
                        "answer",
                        "No response returned."
                    )

                    sources = result.get("sources", [])

                except Exception as exc:

                    answer = f"Chatbot error: {exc}"
                    sources = []

                st.markdown(answer)

                if sources:
                    st.caption("Sources: " + ", ".join(sources))

        st.session_state["chat_messages"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })