"""Pydantic request and response schemas for the public API."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LeadCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    destination: str | None = Field(default=None, max_length=160)
    travel_start: date | None = None
    travel_end: date | None = None
    travelers: int = Field(default=1, ge=1, le=100)
    budget_amount: float | None = Field(default=None, gt=0)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    notes: str | None = Field(default=None, max_length=3000)

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agency_id: str
    customer_name: str
    email: str | None
    phone: str | None
    destination: str | None
    travel_start: date | None
    travel_end: date | None
    travelers: int
    budget_amount: float | None
    currency_code: str
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    task_type: Literal["qualify_lead", "build_offer"]
    lead_id: str
    instructions: str | None = Field(default=None, max_length=3000)


class TaskApprove(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class TaskReject(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class TaskEdit(BaseModel):
    result: dict[str, Any]
    notes: str | None = Field(default=None, max_length=2000)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agency_id: str
    lead_id: str | None
    task_type: str
    title: str
    assigned_agent_id: str
    status: str
    input_data: dict[str, Any]
    result: dict[str, Any]
    confidence: float
    requires_owner_approval: bool
    owner_decision_notes: str | None
    duration_ms: int
    created_at: datetime
    updated_at: datetime
