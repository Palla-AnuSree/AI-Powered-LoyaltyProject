
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    outlet_id: Mapped[int | None] = mapped_column(
        ForeignKey("outlets.id"),
        nullable=True,
        index=True
    )
