"""Service for content analysis and storing moderation logs."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.detection.pipeline import DetectionPipeline
from backend.privacy.pii_masking import PIIMasker
from backend.database.models import ModerationLog

logger = logging.getLogger(__name__)


class AnalyzeService:
    """Handles content analysis and persistence of moderation records."""

    def __init__(self):
        self._pipeline = DetectionPipeline()
        self._pii_masker = PIIMasker()

    def analyze(self, text: str) -> dict:
        """
        Analyze text for harassment. Returns full result dict.
        Does not require DB - use store_result to persist.
        """
        result = self._pipeline.run(text)
        return {
            "language": result.language,
            "classification": result.classification,
            "confidence": result.confidence,
            "pii_detected": result.pii_detected,
            "masked_text": result.masked_text,
            "explanation": result.explanation,
            "severity": result.severity,
        }

    def _get_initial_status(self, classification: str, severity: str) -> str:
        """
        Auto-approve safe+low; auto-delete abusive+high.
        Otherwise requires manual moderation (pending).
        """
        c = (classification or "").lower()
        s = (severity or "").lower()
        if c == "safe" and s == "low":
            return "approved"
        if c == "abusive" and s == "high":
            return "deleted"
        return "pending"

    async def analyze_and_store(
        self, text: str, db: AsyncSession
    ) -> tuple[dict, Optional[int]]:
        """
        Analyze text and store anonymized result in DB.
        Auto-approves safe+low; auto-deletes abusive+high.
        Returns (result_dict, message_id).
        """
        result = self._pipeline.run(text)
        # Never store original text - only hash
        text_hash = self._pii_masker.hash_content(text)

        status = self._get_initial_status(result.classification, result.severity)

        log = ModerationLog(
            original_text_hash=text_hash,
            masked_text=result.masked_text,
            language=result.language,
            classification=result.classification,
            confidence=result.confidence,
            severity=result.severity,
            explanation=result.explanation,
            status=status,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)

        result_dict = {
            "language": result.language,
            "classification": result.classification,
            "confidence": result.confidence,
            "pii_detected": result.pii_detected,
            "masked_text": result.masked_text,
            "explanation": result.explanation,
            "severity": result.severity,
            "message_id": log.id,
            "status": status,
        }
        logger.info("Stored moderation log id=%s classification=%s status=%s", log.id, result.classification, status)
        return result_dict, log.id
