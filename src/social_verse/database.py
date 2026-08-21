from __future__ import annotations

import json
from dataclasses import asdict
from difflib import SequenceMatcher
from pathlib import Path

from .models import NewsItem, PublishedItem


class History:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: list[dict[str, str]] = json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _similar(left: str, right: str) -> bool:
        return SequenceMatcher(None, left.casefold(), right.casefold()).ratio() >= 0.88

    def contains(self, item: NewsItem) -> bool:
        return any(
            record.get("id") == item.id
            or record.get("url") == item.url
            or self._similar(record.get("title", ""), item.title)
            for record in self.records
        )

    def add(self, item: PublishedItem) -> None:
        self.records.append(asdict(item))

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

