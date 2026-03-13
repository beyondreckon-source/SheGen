"""
Harassment classification using Groq LLM with LangChain.
Uses multilingual embeddings for semantic similarity as a fallback/supplement.
"""

import json
import logging
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Classification schema for structured output
CLASSIFICATION_SCHEMA = {
    "classification": "one of: safe, warning, abusive",
    "confidence": "float between 0 and 1",
    "severity": "one of: low, medium, high",
    "explanation": "brief explanation in the same language as the input",
}

CLASSIFICATION_PROMPT = """You are an expert content moderator for a WOMEN harassment detection system (SheGen).
Analyze the following message specifically for harassment, abuse, or harmful content TARGETING WOMEN.

Message (may be in English, Hindi, Malayalam, Tamil, or other languages):
---
{text}
---

Focus on WOMEN-SPECIFIC harassment:
- Sexual harassment, unwanted advances, or objectification of women
- Gender-based abuse, misogyny, or sexist slurs
- Threats, intimidation, or violence directed at women
- Body shaming, slut-shaming, or demeaning women
- Stalking, doxxing, or privacy violations targeting women
- Workplace or online harassment of women
- Domestic violence or controlling language toward women
- Hate speech or discrimination based on gender

General bullying or abuse NOT targeting women specifically = typically "safe" unless severe.

Respond with a JSON object containing exactly these keys:
- classification: "safe" (no women-targeted issues), "warning" (borderline/mild), or "abusive" (clear women-targeted violation)
- confidence: number from 0.0 to 1.0
- severity: "low", "medium", or "high" based on potential harm to women
- explanation: brief explanation in the SAME language as the input (or English if unclear), focusing on women harassment context

JSON only, no other text:"""


class HarassmentClassifier:
    """Uses Groq LLM to classify content for harassment."""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        settings = get_settings()
        self._client = ChatGroq(
            api_key=settings.groq_api_key,
            model=model_name,
            temperature=0.1,
        )
        self._prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        self._parser = JsonOutputParser()

    def classify(self, text: str, language: str = "en") -> dict:
        """
        Classify text for harassment. Returns dict with classification, confidence, severity, explanation.
        """
        if not text or not text.strip():
            return {
                "classification": "safe",
                "confidence": 1.0,
                "severity": "low",
                "explanation": "Empty input.",
            }

        chain = self._prompt | self._client | self._parser

        try:
            result = chain.invoke({"text": text})
            if isinstance(result, dict):
                return self._normalize_result(result)
            if isinstance(result, str):
                s = result.strip()
                if s.startswith("```"):
                    s = s.split("```")[1]
                    if s.startswith("json"):
                        s = s[4:]
                parsed = json.loads(s.strip())
                return self._normalize_result(parsed)
        except Exception as e:
            logger.exception("Classification failed: %s", e)
            return {
                "classification": "warning",
                "confidence": 0.0,
                "severity": "medium",
                "explanation": f"Classification error: {str(e)}",
            }

        return {
            "classification": "warning",
            "confidence": 0.0,
            "severity": "medium",
            "explanation": "Unable to classify.",
        }

    def _normalize_result(self, r: dict) -> dict:
        """Ensure result has expected keys and valid values."""
        classification = str(r.get("classification", "safe")).lower()
        if classification not in ("safe", "warning", "abusive"):
            classification = "warning"

        confidence = float(r.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        severity = str(r.get("severity", "low")).lower()
        if severity not in ("low", "medium", "high"):
            severity = "medium"

        explanation = str(r.get("explanation", "No explanation provided."))

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "explanation": explanation,
        }
