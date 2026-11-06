# Streamlit frontend

## Install
Activate the main project's `.venv`, then from the project root run:
```bash
pip install streamlit requests plotly
```

## Start
Terminal 1:
```bash
uvicorn app.main:app --reload
```
Terminal 2, from the project root:
```bash
streamlit run streamlit_app/Home.py
```
Open http://localhost:8501.

The UI calls `http://127.0.0.1:8000/api/v1` by default. Set `API_BASE_URL` if needed.

The current backend chatbot route is a placeholder until the RAG/LangGraph workflow is implemented. Streamlit page guards improve navigation but are not a security boundary: FastAPI must enforce JWT, role, permission and record-ownership checks on every endpoint.
