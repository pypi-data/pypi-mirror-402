import os
from dotenv import load_dotenv

from dataclasses import dataclass
from typing import Optional

load_dotenv()

# ===== OpenAI / 兼容 API =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ===== LLM 并发限制 =====
MAX_LLM_CONCURRENCY = int(os.getenv("MAX_LLM_CONCURRENCY", "2"))


@dataclass(frozen=True)
class Settings:
    OPENAI_API_KEY: Optional[str] = OPENAI_API_KEY
    OPENAI_BASE_URL: str = OPENAI_BASE_URL
    OPENAI_MODEL: str = OPENAI_MODEL
    MAX_LLM_CONCURRENCY: int = MAX_LLM_CONCURRENCY


# Convenience accessor (for debugging / external scripts)
settings = Settings()
