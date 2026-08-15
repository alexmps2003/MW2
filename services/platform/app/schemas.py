from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import OrderStatus


class OrderCreate(BaseModel):
    client_id: str = Field(min_length=2, max_length=80)
    recipient_name: str = Field(min_length=2, max_length=120)
    delivery_address: str = Field(min_length=5, max_length=500)
    priority: str = Field(default="NORMAL", pattern="^(NORMAL|HIGH)$")


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus
    detail: str | None
    created_at: datetime


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    idempotency_key: str
    client_id: str
    recipient_name: str
    delivery_address: str
    priority: str
    status: OrderStatus
    route_summary: str | None
    failure_step: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    history: list[HistoryResponse]


class IntegrationPreviewResponse(BaseModel):
    order_id: str
    cms_response: str
    wms_response: str
    route_summary: str


class DeliveryUpdate(BaseModel):
    outcome: Literal["DELIVERED", "DELIVERY_FAILED"]
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_failure_reason(self) -> "DeliveryUpdate":
        if self.outcome == "DELIVERY_FAILED" and not self.reason:
            raise ValueError("A reason is required when delivery fails")
        return self
