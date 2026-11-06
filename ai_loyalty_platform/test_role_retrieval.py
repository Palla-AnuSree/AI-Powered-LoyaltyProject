import asyncio

from app.ai.rag.retriever import retrieve_context


TEST_CASES = [
    {
        "role": "admin",
        "question": "What responsibilities does an admin have?",
    },
    {
        "role": "customer",
        "question": "How can a customer earn reward points?",
    },
    {
        "role": "outlet_user",
        "question": "What are the responsibilities of an outlet user?",
    },
    {
        "role": "supervisor",
        "question": "What are the responsibilities of a supervisor?",
    },
    {
        "role": "support",
        "question": "How should support staff handle customer complaints?",
    },
]


async def main():
    for test in TEST_CASES:
        print("\n" + "=" * 60)
        print("Testing role:", test["role"])
        print("Question:", test["question"])

        results = await retrieve_context(
            question=test["question"],
            user_scope={"role": test["role"]},
        )

        if not results:
            print("No documents retrieved.")
            continue

        for result in results:
            print("\nSource:", result["metadata"].get("source"))
            print("Document ID:", result["metadata"].get("document_id"))
            print("Content:", result["content"][:300])


asyncio.run(main())