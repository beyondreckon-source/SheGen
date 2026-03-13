"""Internal API routes for dashboard (hidden from Platform API docs)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.schemas import (
    ModerationActionRequest,
    ModerationAction,
    ModerationQueueResponse,
    ModerationItem,
    ModerationActionType,
)
from backend.services.moderation_service import ModerationService

router = APIRouter(include_in_schema=False)
moderation_service = ModerationService()


def _action_to_str(a: ModerationActionType) -> str:
    return a.value


@router.get("/moderation_queue", response_model=ModerationQueueResponse)
async def get_moderation_queue(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get moderation queue items. Default: pending items."""
    items, total = await moderation_service.get_queue(db, status, limit, offset)
    return ModerationQueueResponse(
        items=[ModerationItem(**x) for x in items],
        total=total,
    )


@router.post("/moderation_action", response_model=ModerationAction)
async def moderation_action(
    request: ModerationActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Apply moderator action: approve, warn_user, escalate, or delete."""
    success, message = await moderation_service.take_action(
        db,
        request.moderation_id,
        _action_to_str(request.action),
        request.notes,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return ModerationAction(
        success=True,
        moderation_id=request.moderation_id,
        action=_action_to_str(request.action),
        message=message,
    )


@router.delete("/moderation_queue")
async def clear_moderation_queue(db: AsyncSession = Depends(get_db)):
    """Delete all moderation records."""
    try:
        count = await moderation_service.clear_all(db)
        return {"success": True, "deleted": count, "message": f"Deleted {count} record(s)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
