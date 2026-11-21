"""Activity and audit logger service for recording candidate workflow actions."""

import uuid
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models import ActivityLog

logger = logging.getLogger("app.services.activity_logger")


def record_activity(
    db: Session,
    user_id: str | None,
    action: str,
    title: str,
    description: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> ActivityLog:
    """Record an audit event for candidate actions across the platform."""
    try:
        activity = ActivityLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    except Exception as exc:
        logger.error("Failed to record activity log: %s", exc)
        db.rollback()
        # Non-blocking fallback
        return ActivityLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            title=title,
            created_at=datetime.now(timezone.utc),
        )
