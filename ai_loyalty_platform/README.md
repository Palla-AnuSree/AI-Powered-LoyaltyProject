# AI-Powered Intelligent Loyalty Management Platform

A Python + FastAPI starter codebase for a loyalty platform with customer support chatbot and an extensible GenAI / Agentic AI architecture.

## Included in this starter
- FastAPI application with modular routers
- PostgreSQL + SQLAlchemy 2.x setup
- JWT authentication and role/permission dependencies
- Customer, loyalty-points and order API foundations
- Order cancellation workflow with eligibility checks and explicit confirmation
- AI module scaffolding for LangChain, RAG, LangGraph agents
- MCP and A2A integration placeholders
- Docker Compose, environment template and basic tests

> This is a learning/portfolio starter, not a production-ready deployment. Before production use, add migrations, refresh-token rotation, robust audit logging, rate limiting, secret management, tenant isolation, stronger authorization tests, and operational monitoring.

## 1. Requirements
- Python 3.11+
- PostgreSQL 15+ (or a compatible PostgreSQL version)
- Docker Desktop (optional)

## 2. Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Update `.env` with your PostgreSQL connection string and a long random `SECRET_KEY`.

Create the database, then run:
```bash
uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

The starter creates tables on application startup for easy local learning. Use Alembic migrations for a serious project.

## 3. First-time admin
For the initial learning setup, register a user through `POST /api/v1/auth/register` with role `admin`. In a real deployment, never allow public self-registration as an administrator; seed the first admin through a secure command or migration.

## 4. Main endpoints
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/token` (OAuth2 password form)
- `GET /api/v1/auth/me`
- `POST /api/v1/customers`
- `GET /api/v1/customers/me`
- `GET /api/v1/loyalty/me/points`
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/cancel`

Cancellation requires `{"confirm": true}` and the authenticated customer must own the order. The service also checks that the order is still in a cancellable state.

## 5. AI roadmap in this repository
1. Implement the business APIs and test them.
2. Add an LLM client in `app/ai/llm/client.py`.
3. Implement document ingestion, chunking, embeddings and PGVector retrieval in `app/ai/rag/`.
4. Build LangChain tools that call the existing service layer (not raw unrestricted SQL).
5. Build LangGraph state, nodes, routing and human approval for cancellation.
6. Expose narrowly scoped tools through MCP servers in `app/mcp/`.
7. Add separate A2A agent services and authenticated task exchange in `app/a2a/`.
8. Add tracing/evaluation, rate limits, retries, idempotency and security tests.

## 6. Important security design
- Never trust a `customer_id`, role, or permission supplied by the LLM.
- Derive the user identity from the verified JWT.
- Apply ownership and outlet/team scope checks in backend services and database queries.
- Treat model output as untrusted input.
- Require explicit confirmation for consequential actions such as cancellation.
- Keep MCP tools narrow and validate every argument server-side.
- Do not expose arbitrary SQL execution to the model.
