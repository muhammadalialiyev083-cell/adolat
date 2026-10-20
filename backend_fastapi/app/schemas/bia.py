"""BIA schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class BIACreate(BaseModel):
    process: int
    mtpd_hours: float = Field(ge=0, allow_inf_nan=False)
    rto_hours: float = Field(ge=0, allow_inf_nan=False)
    rpo_minutes: int = Field(default=60, ge=0)
    backup_interval_minutes: int = Field(default=60, ge=0)
    comments: str = ""


class BIAOut(BaseModel):
    id: int
    process: int
    process_name: str
    revision: int
    mtpd_hours: str
    rto_hours: str
    rpo_minutes: int
    backup_interval_minutes: int
    has_rpo_gap: bool
    status: str
    approved_by_name: Optional[str] = None

    model_config = {"from_attributes": True}
