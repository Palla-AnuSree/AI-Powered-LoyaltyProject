
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        unique=True,
        index=True
    )

    account_number: Mapped[str] = mapped_column(
        String(30), unique=True, index=True
    )

    points_balance: Mapped[int] = mapped_column(
        Integer, default=0
    )

    tier: Mapped[str] = mapped_column(
        String(20), default="Silver"
    )

    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )


class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), index=True
    )

    points: Mapped[int] = mapped_column(Integer)

    transaction_type: Mapped[str] = mapped_column(
        String(20)
    )  # earn, redeem, adjustment

    description: Mapped[str] = mapped_column(
        String(255), default=""
    )
