
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.models import user, customer, order, loyalty, outlet, rag_document,cancellation  # noqa: F401
from app.ai.graph.workflow import build_loyalty_graph
from app.ai.graph.cancellation_workflow import build_cancellation_graph


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create existing application tables
    Base.metadata.create_all(bind=engine)

    # Convert SQLAlchemy URL to PostgreSQL connection URL
    checkpoint_db_url = settings.DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1
    )

    # Keep the PostgreSQL checkpointer alive during application runtime
    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_db_url
    ) as checkpointer:

        # Create checkpoint tables if they do not exist
        await checkpointer.setup()

        # Build LangGraph using PostgreSQL memory
        app.state.loyalty_graph = build_loyalty_graph(checkpointer)

        app.state.cancellation_graph = build_cancellation_graph(checkpointer)

        yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
