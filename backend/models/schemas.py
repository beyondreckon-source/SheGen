"""Request and response schemas for the moderation API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Classification(str, Enum):
    """Content classification levels."""

    SAFE = "safe"
    WARNING = "warning"
    ABUSIVE = "abusive"


class Severity(str, Enum):
    """Severity levels for moderation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModerationActionType(str, Enum):
    """Moderator action types."""

    APPROVE = "approve"
    WARN = "warn_user"
    ESCALATE = "escalate"
    DELETE = "delete"


# --- Request Schemas ---


class AnalyzeRequest(BaseModel):
    """Request body for content analysis."""

    text: str = Field(..., min_length=1, max_length=10000, description="User message to analyze")


class ModerationActionRequest(BaseModel):
    """Request body for moderator action."""

    moderation_id: int = Field(..., gt=0, description="ID of the moderation record")
    action: ModerationActionType = Field(..., description="Action to take")
    notes: Optional[str] = Field(None, max_length=500, description="Optional moderator notes")


# --- Response Schemas ---


class AnalyzeResponse(BaseModel):
    """Response from content analysis."""

    language: str = Field(..., description="Detected language code")
    classification: str = Field(..., description="safe, warning, or abusive")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")
    pii_detected: bool = Field(..., description="Whether PII was found")
    masked_text: str = Field(..., description="Text with PII masked")
    explanation: str = Field(..., description="Human-readable explanation")
    severity: str = Field(..., description="low, medium, or high")
    message_id: Optional[int] = Field(None, description="Stored moderation record ID")
    status: Optional[str] = Field(None, description="approved=auto-approved, deleted=auto-deleted, pending=needs review")


class ModerationItem(BaseModel):
    """Single item in the moderation queue."""

    id: int
    original_text_hash: str = Field(..., description="Hash of original content (anonymized)")
    masked_text: str
    language: str
    classification: str
    confidence: float
    severity: str
    explanation: str
    status: str = Field(..., description="pending, approved, warned, escalated, deleted")
    created_at: datetime


class ModerationQueueResponse(BaseModel):
    """Response for moderation queue endpoint."""

    items: list[ModerationItem]
    total: int


class ModerationAction(BaseModel):
    """Response after moderator action."""

    success: bool
    moderation_id: int
    action: str
    message: str
