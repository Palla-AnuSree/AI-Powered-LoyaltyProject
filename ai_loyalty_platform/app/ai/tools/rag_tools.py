
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.ai.rag.retriever import retrieve_context


@tool
async def search_loyalty_policies(
    question: str,
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Search authorized loyalty policy documents.

    Use this tool for questions about:
    - Terms and conditions
    - Privacy policies
    - Reward rules and eligibility
    - Incentives and campaigns
    - Loyalty program policies

    The user's role is injected automatically to enforce document access.
    """

    user_scope = {
        "role": role
    }

    documents = await retrieve_context(
        question=question,
        user_scope=user_scope,
    )

    if not documents:
        return {
            "success": True,
            "found": False,
            "message": "No relevant authorized policy documents were found."
        }

    return {
        "success": True,
        "found": True,
        "documents": documents
    }
