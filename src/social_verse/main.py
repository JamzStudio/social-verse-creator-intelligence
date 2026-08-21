from __future__ import annotations

from datetime import datetime, timezone

from .analyzer import GeminiAnalyzer, LocalAnalyzer
from .collector import collect_news
from .config import Settings
from .database import History
from .models import PublishedItem
from .publisher import TelegramPublisher


def run() -> None:
    settings = Settings.from_env()
    settings.validate()
    history = History(settings.history_path)
    candidates = [
        item
        for item in collect_news(settings.feeds_path, settings.lookback_hours)
        if not history.contains(item)
    ]
    print(f"Found {len(candidates)} unpublished candidate(s).")

    if settings.dry_run:
        for item in candidates[: settings.max_items_per_run]:
            print(f"[DRY RUN] {item.source}: {item.title} — {item.url}")
        return

    local_analyzer = LocalAnalyzer()
    analyzer = (
        GeminiAnalyzer(settings.gemini_api_key, settings.gemini_model, local_analyzer)
        if settings.gemini_api_key
        else local_analyzer
    )
    publisher = TelegramPublisher(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        settings.telegram_topic_id,
    )
    published = 0
    for item in candidates:
        if published >= settings.max_items_per_run:
            break
        analysis = analyzer.analyze(item)
        if not analysis.relevant or analysis.importance < 3 or not analysis.message:
            continue
        publisher.publish(analysis.message)
        history.add(
            PublishedItem(
                id=item.id,
                title=item.title,
                url=item.url,
                source=item.source,
                publication_date=item.publication_date,
                published_date=datetime.now(timezone.utc).isoformat(),
                category=item.category,
            )
        )
        history.save()
        published += 1
        print(f"Published: {item.title}")

    print(f"Published {published} item(s).")


if __name__ == "__main__":
    run()
