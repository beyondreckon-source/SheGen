"""
Platform API - Two endpoints for social media platform integration.
1. Analyze comment - returns attributes for auto-approve / auto-delete decision
2. Get comments by status - returns list of approved, deleted, warned, etc.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.services.analyze_service import AnalyzeService
from backend.services.moderation_service import ModerationService

router = APIRouter(prefix="/api", tags=["Platform API"])
analyze_service = AnalyzeService()
moderation_service = ModerationService()


# --- Request / Response Schemas ---


class CommentAnalyzeRequest(BaseModel):
    """Incoming comment from social media platform."""

    text: str = Field(..., min_length=1, max_length=10000, description="Comment text from social media to analyze")


class CommentAnalyzeResponse(BaseModel):
    """
    Response for platform to decide: auto-approve, auto-delete, or send to review.
    """

    platform_action: str = Field(
        ...,
        description="Platform decision: 'approve' (auto-post), 'delete' (auto-remove), 'review' (needs moderator)",
    )
    status: str = Field(
        ...,
        description="Stored status: approved | deleted | pending (for dashboard compat)",
    )
    classification: str = Field(..., description="safe | warning | abusive")
    severity: str = Field(..., description="low | medium | high")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence 0-1")
    language: str = Field(..., description="Detected language code")
    explanation: str = Field(..., description="Brief explanation")
    pii_detected: bool = Field(..., description="Whether PII was found and masked")
    masked_text: str = Field(..., description="Text with PII masked")
    message_id: Optional[int] = Field(None, description="Stored record ID")


class CommentItem(BaseModel):
    """Single comment in status list."""

    id: int
    masked_text: str
    language: str
    classification: str
    severity: str
    confidence: float
    explanation: str
    status: str
    created_at: str


class CommentsByStatusResponse(BaseModel):
    """List of comments for the requested status."""

    status: str = Field(..., description="Requested status filter")
    items: list[CommentItem]
    total: int


def _to_platform_action(status: str) -> str:
    """Map stored status to platform action."""
    if status == "approved":
        return "approve"
    if status == "deleted":
        return "delete"
    return "review"


@router.post("/analyze", response_model=CommentAnalyzeResponse)
async def analyze_comment(
    request: CommentAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    **1. Analyze Incoming Comment**

    Send a comment from your social media platform. Returns attributes for the platform to decide:
    - **platform_action: approve** → Auto-approve and post the comment
    - **platform_action: delete** → Auto-delete the comment
    - **platform_action: review** → Send to moderator queue for human review
    """
    try:
        result, _ = await analyze_service.analyze_and_store(request.text, db)
        platform_action = _to_platform_action(result.get("status", "pending"))
        return CommentAnalyzeResponse(
            platform_action=platform_action,
            status=result.get("status", "pending"),
            classification=result["classification"],
            severity=result["severity"],
            confidence=result["confidence"],
            language=result["language"],
            explanation=result["explanation"],
            pii_detected=result["pii_detected"],
            masked_text=result["masked_text"],
            message_id=result.get("message_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comments", response_model=CommentsByStatusResponse)
async def get_comments_by_status(
    status: str = "pending",
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    **2. Get Comments by Status**

    Request comments categorized by status. Use the `status` query parameter:
    - **approved** → Auto-approved comments
    - **deleted** → Auto-deleted comments
    - **warned** → Comments that received a warning
    - **escalated** → Escalated for review
    - **pending** → Awaiting moderator action
    """
    valid_statuses = ("pending", "approved", "deleted", "warned", "escalated")
    status = (status or "pending").lower()
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Use one of: {', '.join(valid_statuses)}",
        )
    try:
        items, total = await moderation_service.get_queue(db, status, limit, offset)
        return CommentsByStatusResponse(
            status=status,
            items=[
                CommentItem(
                    id=x["id"],
                    masked_text=x["masked_text"],
                    language=x["language"],
                    classification=x["classification"],
                    severity=x["severity"],
                    confidence=x["confidence"],
                    explanation=x["explanation"],
                    status=x["status"],
                    created_at=x["created_at"].isoformat() if hasattr(x["created_at"], "isoformat") else str(x["created_at"]),
                )
                for x in items
            ],
            total=total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
