"""Service for moderation queue and moderator actions."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ModerationLog

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"approve", "warn_user", "escalate", "delete"}
ACTION_TO_STATUS = {
    "approve": "approved",
    "warn_user": "warned",
    "escalate": "escalated",
    "delete": "deleted",
}


class ModerationService:
    """Handles moderation queue and actions."""

    async def get_queue(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get moderation queue items. Returns (items, total_count).
        By default returns pending items.
        """
        status_filter = status or "pending"
        q = select(ModerationLog).where(ModerationLog.status == status_filter)
        count_q = select(func.count()).select_from(ModerationLog).where(
            ModerationLog.status == status_filter
        )

        total_result = await db.execute(count_q)
        total = total_result.scalar_one()

        q = q.order_by(ModerationLog.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(q)
        logs = result.scalars().all()

        items = [
            {
                "id": log.id,
                "original_text_hash": log.original_text_hash,
                "masked_text": log.masked_text,
                "language": log.language,
                "classification": log.classification,
                "confidence": log.confidence,
                "severity": log.severity,
                "explanation": log.explanation,
                "status": log.status,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return items, total

    async def take_action(
        self,
        db: AsyncSession,
        moderation_id: int,
        action: str,
        notes: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Execute moderator action. Returns (success, message).
        """
        if action not in VALID_ACTIONS:
            return False, f"Invalid action: {action}"

        result = await db.execute(
            select(ModerationLog).where(ModerationLog.id == moderation_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return False, f"Moderation record {moderation_id} not found"

        if log.status != "pending":
            return False, f"Record already processed (status={log.status})"

        new_status = ACTION_TO_STATUS[action]
        log.status = new_status
        log.moderator_notes = notes
        log.updated_at = datetime.utcnow()

        logger.info("Moderation action: id=%s action=%s", moderation_id, action)
        return True, f"Action '{action}' applied successfully"

    async def clear_all(self, db: AsyncSession) -> int:
        """Delete all moderation records. Returns count of deleted records."""
        from sqlalchemy import delete

        result = await db.execute(delete(ModerationLog))
        count = result.rowcount
        logger.info("Cleared all moderation logs: %d records", count)
        return count
