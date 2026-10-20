"""FR-07, FR-08: Calculation engine endpoints.

NOTE: These endpoints have NO trailing slash (frontend expectation).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.engine import (
    EvaluateRiskRequest, EvaluateRiskResponse,
    EvaluateStrategyRequest, PriorityResponse,
)

router = APIRouter()


@router.post("/priority", response_model=PriorityResponse)
def priority_analysis(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    from app.services.engine import compute_priority_scores
    try:
        return compute_priority_scores(db, current_user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.post("/evaluate-risk", response_model=EvaluateRiskResponse)
def evaluate_risk(
    data: EvaluateRiskRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.engine import evaluate_risk_algorithm
    return evaluate_risk_algorithm(data)


@router.post("/evaluate-strategy")
def evaluate_strategy(
    data: EvaluateStrategyRequest,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    from app.services.engine import evaluate_strategy_algorithm
    try:
        return evaluate_strategy_algorithm(db, data, current_user.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
