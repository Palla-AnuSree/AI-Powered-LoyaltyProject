"""Cancellation agent must use backend eligibility checks and human confirmation."""


async def prepare_cancellation(order_id: int, authenticated_user_id: int) -> dict:
    raise NotImplementedError


async def execute_cancellation(order_id: int, authenticated_user_id: int, confirmed: bool) -> dict:
    if not confirmed:
        return {"status": "awaiting_confirmation"}
    raise NotImplementedError("Call the authorized order service; do not let the LLM update the DB directly.")
