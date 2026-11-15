"""Request and response contracts for engineering runs."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class EngineeringRunCreate(BaseModel):
    workspace: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    prompt: str = Field(min_length=8, max_length=12000)
    max_steps: int = Field(default=12, ge=1, le=24)

class EngineeringRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    agency_id: str
    workspace: str
    prompt: str
    status: str
    mode: str
    summary: str
    logs: list[dict[str, Any]]
    changed_files: list[str]
    created_at: datetime
