from app.ai.rag.vector_store import get_vector_store
from app.core.database import SessionLocal
from app.models.rag_document import RAGDocument


VALID_ROLES = {
    "admin",
    "customer",
    "outlet_user",
    "supervisor",
    "support",
}


async def retrieve_context(
    question: str,
    user_scope: dict
) -> list[dict]:

    # 1. Validate authenticated user's role
    user_role = user_scope.get("role")

    if user_role not in VALID_ROLES:
        raise ValueError("Invalid or missing user role.")

    db = SessionLocal()

    try:
        # 2. Get IDs of active documents accessible to this role
        active_documents = (
            db.query(RAGDocument)
            .filter(RAGDocument.is_active.is_(True))
            .all()
        )

        active_document_ids = [
            document.id
            for document in active_documents
            if user_role in (document.allowed_roles or [])
        ]

    finally:
        db.close()

    # 3. No authorized active documents means no results
    if not active_document_ids:
        return []

    # 4. Search the vector database with both filters
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query=question,
        k=3,
        filter={
            f"allowed_{user_role}": True,
            "document_id": {
                "$in": active_document_ids
            }
        }
    )

    # 5. Return matching chunks
    return [
        {
            "content": document.page_content,
            "metadata": document.metadata
        }
        for document in results
    ]