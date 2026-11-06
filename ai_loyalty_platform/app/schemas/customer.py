from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=2, max_length=50)
    phone: str | None = None


class AdminCustomerCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    temporary_password: str = Field(min_length=8)
    customer_code: str = Field(min_length=2, max_length=50)
    phone: str | None = None


class CustomerResponse(BaseModel):
    id: int
    customer_code: str
    phone: str | None

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    temporary_password: str = Field(min_length=8)
    role: str
    customer_code: str | None = None
    phone: str | None = None
    outlet_id: int | None = None
