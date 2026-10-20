"""Engine / analysis schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EvaluateRiskRequest(BaseModel):
    process_id: int
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    rto_hours: float = Field(ge=0, allow_inf_nan=False)
    rpo_minutes: int = Field(ge=0)
    backup_interval_minutes: int = Field(ge=0)


class EvaluateRiskResponse(BaseModel):
    risk_score: int
    risk_class: str
    rpo_gap: bool
    observations: List[str]


class EvaluateStrategyRequest(BaseModel):
    process_id: Optional[int] = None
    target_rto_hours: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    target_rpo_minutes: Optional[int] = Field(default=None, ge=0)
    strategies: Optional[List[Dict[str, Any]]] = None
    strategy_id: Optional[int] = None


class PriorityOperands(BaseModel):
    impact_norm: float
    urgency_norm: float
    risk_norm: float
    dependency_norm: float


class RankedProcess(BaseModel):
    process_id: int
    process_name: str
    priority_score: float
    operands: PriorityOperands
    weights: Dict[str, float] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    formula_version: str = ""
    explanation: str = ""


class PriorityResponse(BaseModel):
    ranked_processes: List[RankedProcess]
