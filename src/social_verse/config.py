from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_topic_id: int | None
    dry_run: bool
    max_items_per_run: int
    lookback_hours: int
    feeds_path: Path
    history_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        topic = os.getenv("TELEGRAM_TOPIC_ID", "").strip()
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip(),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            telegram_topic_id=int(topic) if topic else None,
            dry_run=_as_bool(os.getenv("DRY_RUN", "false")),
            max_items_per_run=max(1, int(os.getenv("MAX_ITEMS_PER_RUN", "5"))),
            lookback_hours=max(1, int(os.getenv("LOOKBACK_HOURS", "72"))),
            feeds_path=ROOT / "config" / "feeds.json",
            history_path=ROOT / "data" / "published_news.json",
        )

    def validate(self) -> None:
        if self.dry_run:
            return
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
