from langchain_postgres import PGVector

from app.core.config import settings
from app.ai.rag.embeddings import get_embedding_model


def get_vector_store():
    embedding_model = get_embedding_model()

    return PGVector(
        embeddings=embedding_model,
        collection_name="loyalty_documents",
        connection=settings.DATABASE_URL,
        use_jsonb=True,
    )