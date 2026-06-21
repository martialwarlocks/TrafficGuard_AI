from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.database import get_db
from backend.app.models import Violation, Review, User, RoutingDecision
from backend.app.schemas import ReviewCreate, ReviewResponse, ViolationResponse
from backend.app.auth import get_current_user, require_roles
from backend.app.services.audit import log_audit

router = APIRouter(tags=["Review"])


@router.get("/review-queue", response_model=list[ViolationResponse])
async def get_review_queue(
    current_user: User = Depends(require_roles("Admin", "Supervisor", "Officer")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Violation)
        .where(Violation.routing_decision == RoutingDecision.HUMAN_REVIEW)
        .where(Violation.status == "pending")
        .order_by(desc(Violation.detected_at))
        .limit(50)
    )
    return result.scalars().all()


@router.post("/review", response_model=ReviewResponse)
async def submit_review(
    review_data: ReviewCreate,
    current_user: User = Depends(require_roles("Admin", "Supervisor", "Officer")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Violation).where(Violation.id == review_data.violation_id))
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    review = Review(
        violation_id=review_data.violation_id,
        officer_id=current_user.id,
        action=review_data.action,
        notes=review_data.notes,
        review_duration_seconds=review_data.review_duration_seconds,
    )
    db.add(review)

    status_map = {"approve": "approved", "reject": "rejected", "escalate": "escalated"}
    violation.status = status_map.get(review_data.action.value, "reviewed")
    violation.processed_at = datetime.utcnow()

    await log_audit(
        db, f"review.{review_data.action.value}",
        user_id=current_user.id,
        resource_type="violation",
        resource_id=str(violation.id),
    )
    await db.flush()
    return review
