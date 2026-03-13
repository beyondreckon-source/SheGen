"""Language detection for multilingual content."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# langdetect for lightweight detection; supports our target languages
try:
    from langdetect import detect, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

# Supported languages for the system
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ml": "Malayalam",
    "ta": "Tamil",
}


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Returns ISO 639-1 language code (e.g., 'en', 'hi', 'ml', 'ta').
    Falls back to 'en' if detection fails or language is unsupported.
    """
    if not text or not text.strip():
        return "en"

    if not HAS_LANGDETECT:
        logger.warning("langdetect not available, defaulting to 'en'")
        return "en"

    try:
        lang_code = detect(text.strip())
        # Normalize to supported set; map close variants if needed
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
        # For demo, accept any detected lang but log
        return lang_code if lang_code else "en"
    except LangDetectException as e:
        logger.debug("Language detection failed: %s", e)
        return "en"
