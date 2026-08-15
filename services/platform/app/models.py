import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    CMS_CONFIRMED = "CMS_CONFIRMED"
    WMS_ACCEPTED = "WMS_ACCEPTED"
    ROUTE_PLANNED = "ROUTE_PLANNED"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    DELIVERY_FAILED = "DELIVERY_FAILED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    client_id: Mapped[str] = mapped_column(String(80), index=True)
    recipient_name: Mapped[str] = mapped_column(String(120))
    delivery_address: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.RECEIVED)
    cms_done: Mapped[bool] = mapped_column(default=False)
    wms_done: Mapped[bool] = mapped_column(default=False)
    ros_done: Mapped[bool] = mapped_column(default=False)
    route_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_step: Mapped[str | None] = mapped_column(String(40), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    history: Mapped[list["OrderHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderHistory.created_at"
    )


class OrderHistory(Base):
    __tablename__ = "order_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    order: Mapped[Order] = relationship(back_populates="history")

