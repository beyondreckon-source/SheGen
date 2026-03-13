"""
End-to-end detection pipeline:
1. Detect language
2. Mask PII
3. Generate embeddings (optional, for future use)
4. Classify harassment via Groq LLM
5. Return structured result
"""

import logging
from dataclasses import dataclass
from typing import Optional

from backend.detection.language import detect_language
from backend.detection.classifier import HarassmentClassifier
from backend.privacy.pii_masking import PIIMasker

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of the full detection pipeline."""

    language: str
    classification: str
    confidence: float
    pii_detected: bool
    masked_text: str
    explanation: str
    severity: str


class DetectionPipeline:
    """Orchestrates the full harassment detection pipeline."""

    def __init__(self):
        self._pii_masker = PIIMasker()
        self._classifier = HarassmentClassifier()

    def run(self, text: str) -> DetectionResult:
        """
        Execute the full pipeline on input text.
        Only masked content is sent to the LLM.
        """
        if not text or not text.strip():
            return DetectionResult(
                language="en",
                classification="safe",
                confidence=1.0,
                pii_detected=False,
                masked_text="",
                explanation="Empty input.",
                severity="low",
            )

        # Step 1: Detect language (on original text for better accuracy)
        language = detect_language(text)
        logger.debug("Detected language: %s", language)

        # Step 2: Mask PII before sending to LLM
        masked_text, pii_detected = self._pii_masker.mask(text)

        # Step 3: Embeddings (optional - for future semantic search / hybrid scoring)
        # compute_embedding(masked_text)  # Can store for similarity search later

        # Step 4: Classify via Groq LLM (only masked content)
        classification_result = self._classifier.classify(masked_text, language)

        return DetectionResult(
            language=language,
            classification=classification_result["classification"],
            confidence=classification_result["confidence"],
            pii_detected=pii_detected,
            masked_text=masked_text,
            explanation=classification_result["explanation"],
            severity=classification_result["severity"],
        )
