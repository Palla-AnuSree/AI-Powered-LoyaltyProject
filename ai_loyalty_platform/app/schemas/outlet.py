from pydantic import BaseModel, Field


class OutletCreate(BaseModel):
    outlet_code: str = Field(min_length=2, max_length=50)
    outlet_name: str = Field(min_length=2, max_length=150)
    address: str | None = None
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)


class OutletResponse(BaseModel):
    id: int
    outlet_code: str
    outlet_name: str
    address: str | None
    city: str
    state: str
    is_active: bool

    model_config = {"from_attributes": True}
