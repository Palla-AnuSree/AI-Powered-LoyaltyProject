# MCP implementation plan
Create MCP servers that expose narrow, validated tools:
- Order MCP: get_order_status, check_cancellation_eligibility, request_cancel_order
- Loyalty MCP: get_points_balance, get_points_history, list_rewards
- Reporting MCP: get_outlet_sales, get_target_achievement

Each tool must authenticate/authorize the caller, validate ownership/scope, log actions,
and call the application service layer. Do not expose arbitrary SQL or unrestricted admin tools.
