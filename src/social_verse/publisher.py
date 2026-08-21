from __future__ import annotations

import requests


class TelegramPublisher:
    def __init__(self, token: str, chat_id: str, topic_id: int | None) -> None:
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id
        self.topic_id = topic_id

    def publish(self, message: str) -> None:
        payload: dict[str, str | int] = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": "true",
            "disable_notification": "true",
        }
        if self.topic_id is not None:
            payload["message_thread_id"] = self.topic_id
        response = requests.post(self.url, data=payload, timeout=30)
        response.raise_for_status()
