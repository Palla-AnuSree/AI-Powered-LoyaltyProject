
"""RAG ingestion pipeline: load -> clean -> chunk -> embed -> store."""

from pathlib import Path

from pypdf import PdfReader
import docx2txt
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.database import SessionLocal
from app.models.rag_document import RAGDocument
from app.ai.rag.vector_store import get_vector_store

from uuid import uuid4
from sqlalchemy import func



def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    elif extension == ".docx":
        text = docx2txt.process(str(path))

    elif extension == ".txt":
        text = path.read_text(encoding="utf-8")

    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX or TXT.")

    if not text.strip():
        raise ValueError("No readable text found in the document.")

    return text


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_into_chunks(text: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    return splitter.split_text(text)


async def ingest_document(
    file_path: str,
    allowed_roles: list[str]
) -> dict:

    valid_roles = {
        "admin",
        "customer",
        "outlet_user",
        "supervisor",
        "support"
    }

    # 1. Validate roles
    if not allowed_roles:
        raise ValueError("At least one allowed role must be provided.")

    if not set(allowed_roles).issubset(valid_roles):
        raise ValueError("One or more invalid roles provided.")

    allowed_roles = sorted(set(allowed_roles))

    # 2. Load and process document
    text = load_document(file_path)
    cleaned_text = clean_text(text)
    chunks = split_into_chunks(cleaned_text)

    file_name = Path(file_path).name

    db = SessionLocal()
    
    chunk_ids = []
    document_record = None
    vector_store = None

    try:
        vector_store = get_vector_store()
        # 3. Calculate next document version
        latest_version = (
            db.query(func.max(RAGDocument.version))
            .filter(RAGDocument.file_name == file_name)
            .scalar()
        )

        new_version = (latest_version or 0) + 1

        # 4. Create new inactive document record
        document_record = RAGDocument(
            file_name=file_name,
            version=new_version,
            is_active=False,
            allowed_roles=allowed_roles,
        )

        db.add(document_record)
        db.commit()
        db.refresh(document_record)

        # 5. Create chunks with document version metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": file_path,
                    "chunk_index": index,
                    "document_id": document_record.id,
                    "version": new_version,
                    **{
                        f"allowed_{role}": role in allowed_roles
                        for role in [
                            "admin",
                            "customer",
                            "outlet_user",
                            "supervisor",
                            "support",
                        ]
                    },
                }
            )
            for index, chunk in enumerate(chunks)
        ]

        # 6. Generate unique IDs for the chunks
        chunk_ids = [str(uuid4()) for _ in documents]

        # 7. Store the new chunks
        vector_store.add_documents(
            documents,
            ids=chunk_ids
        )

        # 8. Activate the new version
        old_versions = (
            db.query(RAGDocument)
            .filter(
                RAGDocument.file_name == file_name,
                RAGDocument.is_active.is_(True)
            )
            .all()
        )

        for old_version in old_versions:
            old_version.is_active = False

        document_record.is_active = True
        db.commit()

        return {
            "message": "Document ingested successfully",
            "file_name": file_name,
            "document_id": document_record.id,
            "version": new_version,
            "total_chunks": len(chunks),
            "allowed_roles": allowed_roles,
        }

    except Exception:
        if chunk_ids and vector_store is not None:
            vector_store.delete(ids=chunk_ids)

        db.rollback()

        if document_record is not None:
            existing_record = db.get(RAGDocument, document_record.id)

            if existing_record is not None:
                db.delete(existing_record)
                db.commit()

        raise

    finally:
        db.close()