from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NewsItem:
    id: str
    title: str
    url: str
    source: str
    category: str
    publication_date: str
    excerpt: str


@dataclass(frozen=True)
class PublishedItem:
    id: str
    title: str
    url: str
    source: str
    publication_date: str
    published_date: str
    category: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

