"""PII detection and masking - ensures no sensitive data reaches the LLM or logs."""

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PIIMatch:
    """Represents a detected PII entity."""

    value: str
    type: str
    start: int
    end: int
    masked: str


class PIIMasker:
    """
    Detects and masks personally identifiable information (PII) in text.
    Supports: emails, phone numbers (Indian formats), generic numbers.
    """

    # Patterns for PII detection
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    PHONE_INDIAN = re.compile(
        r"(?:\+91[- ]?)?[6-9]\d{9}\b|(?:\+91[- ]?)?[6-9]\d{2}[- ]?\d{3}[- ]?\d{4}\b"
    )
    PHONE_GENERIC = re.compile(
        r"\b(?:\+\d{1,3}[- ]?)?\(?\d{2,4}\)?[- ]?\d{3,4}[- ]?\d{3,4}\b"
    )

    PLACEHOLDERS = {
        "email": "[EMAIL_REDACTED]",
        "phone": "[PHONE_REDACTED]",
        "number": "[NUMBER_REDACTED]",
    }

    def detect(self, text: str) -> list[PIIMatch]:
        """Detect all PII in the given text."""
        matches: list[PIIMatch] = []

        for pattern, pii_type, placeholder in [
            (self.EMAIL_PATTERN, "email", self.PLACEHOLDERS["email"]),
            (self.PHONE_INDIAN, "phone", self.PLACEHOLDERS["phone"]),
            (self.PHONE_GENERIC, "number", self.PLACEHOLDERS["number"]),
        ]:
            for m in pattern.finditer(text):
                # Avoid duplicate matches (e.g., Indian phone could match generic)
                if any(
                    m.start() >= existing.start and m.end() <= existing.end
                    for existing in matches
                ):
                    continue
                matches.append(
                    PIIMatch(
                        value=m.group(),
                        type=pii_type,
                        start=m.start(),
                        end=m.end(),
                        masked=placeholder,
                    )
                )

        # Sort by position for correct replacement order
        matches.sort(key=lambda x: x.start)
        return matches

    def mask(self, text: str) -> tuple[str, bool]:
        """
        Mask all PII in text. Returns (masked_text, pii_detected).
        """
        matches = self.detect(text)
        if not matches:
            return text, False

        # Build masked string by replacing from end to start (preserves indices)
        result = list(text)
        for m in reversed(matches):
            result[m.start : m.end] = list(m.masked)

        masked_text = "".join(result)
        logger.debug("Masked %d PII entities", len(matches))
        return masked_text, True

    @staticmethod
    def hash_content(text: str) -> str:
        """Create a secure hash of content for logging (no reversible storage)."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mask_pii(text: str) -> tuple[str, bool]:
    """Convenience function to mask PII in text."""
    masker = PIIMasker()
    return masker.mask(text)
