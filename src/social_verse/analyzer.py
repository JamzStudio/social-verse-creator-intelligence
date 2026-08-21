from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

import requests

from .models import NewsItem


@dataclass(frozen=True)
class Analysis:
    relevant: bool
    importance: int
    message: str


# Local deterministic rules: no paid API, trial credit, account, or remote AI.
HIGH_VALUE_TERMS = {
    "algorithm", "analytics", "creator", "editing", "feature", "instagram",
    "monetization", "reels", "shorts", "tool", "video", "youtube", "ai",
    "هوش مصنوعی", "الگوریتم", "درآمد", "کریتور", "قابلیت", "ویدیو",
}
HIGH_IMPACT_TERMS = {
    "algorithm", "monetization", "policy", "launch", "released", "available",
    "الگوریتم", "درآمدزایی", "انتشار", "عرضه", "قانون",
}
LOW_VALUE_TERMS = {"award", "event", "hiring", "podcast", "quarterly", "sponsorship"}

CATEGORY_GUIDANCE = {
    "instagram_meta": (
        "این تغییر می‌تونه روی تولید یا انتشار محتوای اینستاگرام اثر بذاره.",
        "قبل از اینکه کل برنامه‌ت رو عوض کنی، قابلیت جدید رو روی ۳ محتوای بعدی امتحان کن و نتیجه‌ش رو با محتوای قبلی مقایسه کن.",
    ),
    "youtube": (
        "برای سازنده‌های یوتیوب، این خبر می‌تونه روی ساخت ویدیو، Shorts یا عملکرد کانال اثر داشته باشه.",
        "اول تغییر رو روی یک ویدیو یا Short آزمایش کن؛ بعد آمار بازدید، نگهداشت مخاطب و تعامل رو با نمونه‌های قبلی بسنج.",
    ),
    "ai_tools": (
        "این ابزار یا تغییر تازه می‌تونه بخشی از روند ایده‌پردازی، تولید یا ادیت محتوا رو سریع‌تر کنه.",
        "با یک پروژهٔ کم‌ریسک امتحانش کن و زمان، کیفیت خروجی و محدودیت‌هاش رو یادداشت کن؛ بعد دربارهٔ ورودش به روند اصلی کارت تصمیم بگیر.",
    ),
}


def _plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", html.unescape(value))
    return re.sub(r"\s+", " ", value).strip()


class LocalAnalyzer:
    """Zero-cost local relevance filter and conversational message composer."""

    def analyze(self, item: NewsItem) -> Analysis:
        text = f"{item.title} {_plain_text(item.excerpt)}".casefold()
        matches = sum(term in text for term in HIGH_VALUE_TERMS)
        low_value = any(term in text for term in LOW_VALUE_TERMS)
        importance = min(5, 2 + matches + int(any(term in text for term in HIGH_IMPACT_TERMS)))
        relevant = matches > 0 and not (low_value and matches < 2)
        impact, action = CATEGORY_GUIDANCE.get(
            item.category,
            (
                "این خبر ممکنه روی کار کریتورها و تیم‌های محتوا اثر بذاره.",
                "خبر رو بررسی کن و فقط اگه به هدف محتوایی فعلیت ربط داشت، در یک آزمایش کوچک ازش استفاده کن.",
            ),
        )
        excerpt = _plain_text(item.excerpt)
        happened = excerpt[:420].rstrip(" .") if excerpt else item.title
        message = (
            f"🔥 {item.title}\n\n"
            f"چه اتفاقی افتاد؟\n{happened}\n\n"
            f"چرا برای کریتورها مهمه؟\n{impact}\n\n"
            f"حالا چی‌کار کنیم؟\n{action}\n\n"
            f"🔗 منبع: {item.url}"
        )
        return Analysis(relevant=relevant, importance=importance, message=message)


GEMINI_PROMPT = """نقش تو استراتژیست محتوای فارسی Social Verse است.
خبر ورودی را برای کریتورها، ادیتورها، مارکترها و تیم‌های محتوا بررسی کن.
خبر کم‌اهمیت، تبلیغاتی، قدیمی یا نامرتبط را رد کن و متن منبع را کپی نکن.
فقط یک JSON معتبر با کلیدهای relevant (boolean)، importance (عدد ۱ تا ۵) و message برگردان.
اگر خبر مرتبط بود، message را کاملاً فارسی، کوتاه، دقیق و با این قالب بنویس:
🔥 <عنوان کوتاه فارسی>

چه اتفاقی افتاد؟
...

چرا برای کریتورها مهمه؟
...

حالا چی‌کار کنیم؟
...

🔗 منبع: <URL>

لحن همهٔ خبرها و آموزش‌ها محاوره‌ای، گرم و حرفه‌ای باشه؛ مثل توضیح یک دوست آگاه.
از لحن اداری، کلیک‌بیت، اغراق و اصطلاحات انگلیسی غیرضروری دوری کن.
بخش آموزشی باید ساده، مستقیم، قابل اجرا و در صورت نیاز مرحله‌به‌مرحله باشه.
ادعایی خارج از اطلاعات ورودی نساز و حتماً یک اقدام عملی مشخص پیشنهاد بده."""


class GeminiAnalyzer:
    """Optional quality layer; always falls back to the zero-cost local analyzer."""

    def __init__(self, api_key: str, model: str, fallback: LocalAnalyzer) -> None:
        self.api_key = api_key
        self.model = model
        self.fallback = fallback

    def analyze(self, item: NewsItem) -> Analysis:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": f"{GEMINI_PROMPT}\n\nخبر ورودی:\n{json.dumps(item.__dict__, ensure_ascii=False)}"}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        try:
            response = requests.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            analysis = Analysis(
                relevant=bool(data.get("relevant", False)),
                importance=max(1, min(5, int(data.get("importance", 1)))),
                message=str(data.get("message", "")).strip(),
            )
            if analysis.relevant and not analysis.message:
                raise ValueError("Gemini returned an empty message")
            return analysis
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
            print(f"Warning: Gemini unavailable; using local analysis: {error}")
            return self.fallback.analyze(item)
