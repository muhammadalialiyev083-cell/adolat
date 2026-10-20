"""Risk schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class RiskCreate(BaseModel):
    process: int
    asset: Optional[int] = None
    threat: str
    vulnerability: str = ""
    likelihood: int = 3
    impact: int = 3
    likelihood_residual: Optional[int] = Field(default=None, ge=1, le=5)
    impact_residual: Optional[int] = Field(default=None, ge=1, le=5)


class RiskOut(BaseModel):
    id: int
    process_name: str
    asset_name: Optional[str] = None
    threat: str
    likelihood: int
    impact: int
    likelihood_residual: Optional[int] = Field(default=None, ge=1, le=5)
    impact_residual: Optional[int] = Field(default=None, ge=1, le=5)
    risk_score: int
    residual_risk_score: Optional[int] = None
    risk_reduction: int
    risk_class: str
    status: str

    model_config = {"from_attributes": True}


class ControlOut(BaseModel):
    id: int
    risk_id: int
    title: str
    description: str
    status: str
    effectiveness_evidence: str

    model_config = {"from_attributes": True}
