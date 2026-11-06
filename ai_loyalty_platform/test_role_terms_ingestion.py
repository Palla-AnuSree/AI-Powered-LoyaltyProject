import asyncio

from app.ai.rag.ingestion import ingest_document


DOCUMENTS = [
    {
        "file_path": "sample_documents/admin_terms.txt",
        "allowed_roles": ["admin"],
    },
    {
        "file_path": "sample_documents/customer_terms.txt",
        "allowed_roles": ["customer"],
    },
    {
        "file_path": "sample_documents/outlet_user_terms.txt",
        "allowed_roles": ["outlet_user"],
    },
    {
        "file_path": "sample_documents/supervisor_terms.txt",
        "allowed_roles": ["supervisor"],
    },
    {
        "file_path": "sample_documents/support_terms.txt",
        "allowed_roles": ["support"],
    },
]


async def main():
    for document in DOCUMENTS:
        result = await ingest_document(
            file_path=document["file_path"],
            allowed_roles=document["allowed_roles"],
        )

        print("\nIngestion Result:")
        print(result)


asyncio.run(main())