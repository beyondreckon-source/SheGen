"""SQLAlchemy ORM models for moderation logs."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Index

from backend.database.db import Base


class ModerationLog(Base):
    """Stores anonymized moderation records."""

    __tablename__ = "moderation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Store only hash of original content - never store raw PII
    original_text_hash = Column(String(64), nullable=False, index=True)
    masked_text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    classification = Column(String(20), nullable=False)  # safe, warning, abusive
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high
    explanation = Column(Text, nullable=False)
    # Moderation workflow status
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, warned, escalated, deleted
    moderator_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_moderation_status", "status"), Index("ix_moderation_created", "created_at"))

    def __repr__(self) -> str:
        return f"<ModerationLog(id={self.id}, classification={self.classification}, status={self.status})>"
