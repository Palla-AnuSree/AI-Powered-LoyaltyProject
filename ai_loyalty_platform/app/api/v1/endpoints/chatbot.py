from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from app.core.dependencies import require_password_change_completed
from app.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(require_password_change_completed)
):
    try:
        session_id = payload.session_id or str(uuid4())
        thread_id = f"user-{user.id}-session-{session_id}"

        # Get PostgreSQL-backed LangGraph instance
        loyalty_graph = request.app.state.loyalty_graph

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = await loyalty_graph.ainvoke(
            {
                "messages": [HumanMessage(content=payload.message)],
                "user_id": user.id,
                "role": user.role,
                "outlet_id": user.outlet_id,
            },
            config=config,
        )

        return {
            "session_id": session_id,
            "answer": result["response"],
            "user_role": user.role,
            "ai_enabled": True,
            "sources": [
                doc["metadata"].get("source")
                for doc in result.get("retrieved_context", [])
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot error: {str(e)}"
        )
