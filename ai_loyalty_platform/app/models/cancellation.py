
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CancellationRequest(Base):
    __tablename__ = "cancellation_requests"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), index=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), index=True
    )

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    cancellation_reason: Mapped[str] = mapped_column(
        Text
    )

    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )

    thread_id: Mapped[str | None] = mapped_column(
        String(150),
        index=True,
        nullable=True
    )

    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
