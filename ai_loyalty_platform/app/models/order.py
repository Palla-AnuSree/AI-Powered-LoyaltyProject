
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), index=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="placed"
    )

    reward_name: Mapped[str] = mapped_column(
        String(150)
    )

    points_used: Mapped[int] = mapped_column(
        Integer
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
