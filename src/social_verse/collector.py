from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import mktime
from urllib.parse import urldefrag

import feedparser

from .models import NewsItem


def _published_at(entry: object) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return None
    return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)


def collect_news(feeds_path: Path, lookback_hours: int) -> list[NewsItem]:
    feeds = json.loads(feeds_path.read_text(encoding="utf-8"))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    items: list[NewsItem] = []

    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        if getattr(parsed, "bozo", False) and not parsed.entries:
            print(f"Warning: could not read feed {feed['name']}: {parsed.bozo_exception}")
            continue
        for entry in parsed.entries:
            published = _published_at(entry)
            if published and published < cutoff:
                continue
            url = urldefrag(getattr(entry, "link", "").strip()).url
            title = getattr(entry, "title", "").strip()
            if not url or not title:
                continue
            item_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
            items.append(
                NewsItem(
                    id=item_id,
                    title=title,
                    url=url,
                    source=feed["name"],
                    category=feed["category"],
                    publication_date=published.isoformat() if published else "",
                    excerpt=getattr(entry, "summary", "")[:3000],
                )
            )

    return sorted(items, key=lambda item: item.publication_date, reverse=True)

