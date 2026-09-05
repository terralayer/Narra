from collections import defaultdict
from dataclasses import dataclass
from .subjects import parse_subject


@dataclass(slots=True)
class ArticleRecord:
    article_number: int
    message_id: str
    subject: str
    bytes: int = 0


@dataclass(slots=True)
class GroupedRelease:
    key: str
    title: str
    articles: list[ArticleRecord]
    completion: float


def _key(subject: str) -> str:
    parsed = parse_subject(subject)
    value = parsed.filename.lower()
    for ext in ('.m4b', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.rar', '.7z'):
        value = value.replace(ext, '')
    return ' '.join(value.replace('_', ' ').replace('.', ' ').split())


def group_articles(articles: list[ArticleRecord]) -> list[GroupedRelease]:
    buckets: dict[str, list[ArticleRecord]] = defaultdict(list)
    for article in articles:
        buckets[_key(article.subject)].append(article)

    releases: list[GroupedRelease] = []
    for key, items in buckets.items():
        expected = max((parse_subject(a.subject).segment_total or 1) for a in items)
        present = len({parse_subject(a.subject).segment or a.article_number for a in items})
        completion = min(1.0, present / expected) if expected else 0.0
        title = parse_subject(items[0].subject).filename
        releases.append(GroupedRelease(key, title, sorted(items, key=lambda a: a.article_number), completion))
    return releases
