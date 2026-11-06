from services.api_client import api_request

def list_orders():
    return api_request("GET", "/orders")

def cancel_order(order_id):
    return api_request("POST", f"/orders/{order_id}/cancel", json={"confirm": True})
