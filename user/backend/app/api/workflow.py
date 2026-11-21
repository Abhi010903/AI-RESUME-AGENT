"""REST API endpoints for Candidate Workflow Engine and Activity Feed."""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import ActivityLog, User
from app.schemas import ActivityLogResponse, WorkflowStatusResponse
from app.services.workflow_engine import compute_candidate_workflow_status

logger = logging.getLogger("app.api.workflow")

router = APIRouter(prefix="/api/v1/workflow", tags=["Candidate Workflow Engine"])


@router.get(
    "/status",
    response_model=WorkflowStatusResponse,
    summary="Get candidate workflow status and recommended action",
)
def get_workflow_status(
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
) -> WorkflowStatusResponse:
    """Compute and return candidate lifecycle stages, completion metrics, and state-based next action."""
    return compute_candidate_workflow_status(db=db, user=current_user)


@router.get(
    "/activity",
    response_model=list[ActivityLogResponse],
    summary="Get recent candidate activity history",
)
def get_activity_feed(
    db: Annotated[Session, Depends(get_db)],
    current_user: User | None = Depends(get_current_user_optional),
    limit: int = Query(20, ge=1, le=100),
) -> list[ActivityLog]:
    """Retrieve chronologically ordered candidate activity and audit events."""
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc())
    if current_user:
        stmt = stmt.where((ActivityLog.user_id == current_user.id) | (ActivityLog.user_id.is_(None)))
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())
