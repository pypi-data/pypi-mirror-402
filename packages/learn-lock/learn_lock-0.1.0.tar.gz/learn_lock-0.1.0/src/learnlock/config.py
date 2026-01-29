"""Configuration for learn-lock. All configurable values in one place."""

import os
from pathlib import Path

# ============ PATHS ============
DATA_DIR = Path(os.getenv("LEARNLOCK_DATA_DIR", Path.home() / ".learnlock"))
DB_PATH = DATA_DIR / "data.db"

# ============ LLM MODELS ============
GROQ_MODEL = os.getenv("LEARNLOCK_GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_MODEL = os.getenv("LEARNLOCK_GEMINI_MODEL", "gemini-2.5-flash")

# ============ LLM PARAMETERS ============
LLM_MAX_TOKENS = int(os.getenv("LEARNLOCK_LLM_MAX_TOKENS", "2000"))
LLM_TEMPERATURE = float(os.getenv("LEARNLOCK_LLM_TEMPERATURE", "0.3"))
CONTENT_MAX_CHARS = int(os.getenv("LEARNLOCK_CONTENT_MAX_CHARS", "8000"))
CONTENT_TRUNCATE_FOR_PROMPT = int(os.getenv("LEARNLOCK_CONTENT_TRUNCATE_FOR_PROMPT", "6000"))

# ============ SPACED REPETITION (SM-2) ============
SM2_INITIAL_EASE = float(os.getenv("LEARNLOCK_SM2_INITIAL_EASE", "2.5"))
SM2_INITIAL_INTERVAL = float(os.getenv("LEARNLOCK_SM2_INITIAL_INTERVAL", "1.0"))
SM2_MIN_EASE = float(os.getenv("LEARNLOCK_SM2_MIN_EASE", "1.3"))
SM2_MAX_INTERVAL = float(os.getenv("LEARNLOCK_SM2_MAX_INTERVAL", "180"))

# ============ MASTERY THRESHOLDS ============
MASTERY_MIN_EASE = float(os.getenv("LEARNLOCK_MASTERY_MIN_EASE", "2.5"))
MASTERY_MIN_REVIEWS = int(os.getenv("LEARNLOCK_MASTERY_MIN_REVIEWS", "3"))

# ============ GRADING ============
SCORE_MIN = int(os.getenv("LEARNLOCK_SCORE_MIN", "1"))
SCORE_MAX = int(os.getenv("LEARNLOCK_SCORE_MAX", "5"))
SCORE_PASS_THRESHOLD = int(os.getenv("LEARNLOCK_SCORE_PASS_THRESHOLD", "3"))
DEFAULT_FALLBACK_SCORE = int(os.getenv("LEARNLOCK_DEFAULT_FALLBACK_SCORE", "3"))

# ============ EXTRACTION ============
MIN_CONCEPTS = int(os.getenv("LEARNLOCK_MIN_CONCEPTS", "8"))
MAX_CONCEPTS = int(os.getenv("LEARNLOCK_MAX_CONCEPTS", "12"))
EXTRACTION_MAX_RETRIES = int(os.getenv("LEARNLOCK_EXTRACTION_MAX_RETRIES", "2"))

# ============ TEXT LIMITS ============
MAX_CONCEPT_NAME_LENGTH = int(os.getenv("LEARNLOCK_MAX_CONCEPT_NAME_LENGTH", "200"))
MAX_QUOTE_LENGTH = int(os.getenv("LEARNLOCK_MAX_QUOTE_LENGTH", "500"))
MAX_EXPLANATION_LENGTH = int(os.getenv("LEARNLOCK_MAX_EXPLANATION_LENGTH", "2000"))
MAX_FEEDBACK_LENGTH = int(os.getenv("LEARNLOCK_MAX_FEEDBACK_LENGTH", "500"))
MAX_COVERED_MISSED_ITEMS = int(os.getenv("LEARNLOCK_MAX_COVERED_MISSED_ITEMS", "5"))
MAX_COVERED_MISSED_LENGTH = int(os.getenv("LEARNLOCK_MAX_COVERED_MISSED_LENGTH", "200"))
