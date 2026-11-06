from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    order_number: str = Field(min_length=3, max_length=50)
    reward_name: str = Field(min_length=2, max_length=150)
    points_used: int = Field(gt=0)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    status: str
    reward_name: str
    points_used: int

    model_config = {"from_attributes": True}


class CancelOrderRequest(BaseModel):
    confirm: bool
