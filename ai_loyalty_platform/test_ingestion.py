import asyncio

from app.ai.rag.ingestion import ingest_document


async def main():
    result = await ingest_document(
        file_path="sample_loyalty_policy.txt",
        allowed_roles=[
            "admin",
            "support",
        ]
    )
    print(result)


asyncio.run(main())