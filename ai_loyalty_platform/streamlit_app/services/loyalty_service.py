from services.api_client import api_request

def get_my_points():
    return api_request("GET", "/loyalty/me/points")
