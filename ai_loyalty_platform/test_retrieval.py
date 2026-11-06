import asyncio

from app.ai.rag.retriever import retrieve_context


async def main():
    question = "How many points do I earn for spending 100 rupees?"

    results = await retrieve_context(
        question=question,
        user_scope={
            "role": "outlet_user"
        }
    )

    print("\nRetrieved Documents:\n")

    for index, result in enumerate(results, start=1):
        print(f"Result {index}:")
        print(result["content"])
        print("Metadata:", result["metadata"])
        print("-" * 50)


asyncio.run(main())