"""LLM client placeholder.

Next step: configure ChatOpenAI using settings.OPENAI_API_KEY and settings.OPENAI_MODEL.
Keep provider calls behind this module so the rest of the application is provider-agnostic.
"""


from langchain_groq import ChatGroq
from app.core.config import settings


def get_chat_model():
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing in .env")

    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )
