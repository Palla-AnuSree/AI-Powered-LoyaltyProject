
import json

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from app.ai.graph.state import LoyaltyAgentState
from app.ai.llm.client import get_chat_model
from app.ai.llm.prompts import LOYALTY_SUPPORT_SYSTEM_PROMPT
from app.ai.tools.rag_tools import search_loyalty_policies
from app.ai.tools.loyalty_tools import (
    get_customer_points_balance,
    get_customer_transaction_history,
    get_customer_redemption_history,
    get_customer_order_status,
)


tools = [
    get_customer_points_balance,
    get_customer_transaction_history,
    get_customer_redemption_history,
    get_customer_order_status,
    search_loyalty_policies,
]



async def agent_node(state: LoyaltyAgentState):

    llm = get_chat_model().bind_tools(tools)

    response = await llm.ainvoke(
        [
            SystemMessage(content=LOYALTY_SUPPORT_SYSTEM_PROMPT),
            *state["messages"],
        ]
    )

    # If the AI has finished responding, save its answer
    if not response.tool_calls:
        retrieved_context = []

        # Collect results returned by the RAG tool
        for message in state["messages"]:
            if (
                getattr(message, "name", None)
                == "search_loyalty_policies"
            ):
                try:
                    result = json.loads(message.content)

                    if result.get("found"):
                        retrieved_context.extend(
                            result.get("documents", [])
                        )

                except (json.JSONDecodeError, TypeError):
                    pass

        return {
            "messages": [response],
            "response": response.content,
            "retrieved_context": retrieved_context,
        }

    return {
        "messages": [response]
    }


def build_loyalty_graph(checkpointer):

    builder = StateGraph(LoyaltyAgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=checkpointer)
