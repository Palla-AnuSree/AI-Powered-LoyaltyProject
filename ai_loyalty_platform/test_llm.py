from app.ai.llm.client import get_chat_model

llm = get_chat_model()

response = llm.invoke(
    "Explain loyalty points in two simple sentences."
)

print(response.content)