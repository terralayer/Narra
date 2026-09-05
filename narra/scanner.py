from sqlalchemy import select
from sqlalchemy.orm import Session

from .classifier import classify_release
from .grouping import ArticleRecord, group_articles
from .models import NNTPProvider, Release, ReleaseFile, UsenetArticle, UsenetGroup
from .nntp import ProviderConfig, scan_overview
from .subjects import parse_subject


def scan_group(db: Session, provider: NNTPProvider, group: UsenetGroup, limit: int = 5000) -> dict:
    start = max(1, int(group.high_water or 0) + 1)
    config = ProviderConfig(
        host=provider.host,
        port=provider.port,
        username=provider.username,
        password=provider.password,
        use_ssl=provider.use_ssl,
    )
    rows, server_high = scan_overview(config, group.name, start, start + max(1, limit) - 1)
    if not rows:
        group.high_water = max(group.high_water or 0, server_high)
        db.commit()
        return {'articles': 0, 'releases': 0, 'accepted': 0, 'high_water': group.high_water}

    article_records = [
        ArticleRecord(
            article_number=row['article_number'],
            message_id=row['message_id'],
            subject=row['subject'],
            bytes=row['bytes'],
        )
        for row in rows
        if row['message_id']
    ]

    grouped = group_articles(article_records)
    accepted_count = 0
    release_count = 0
    for candidate in grouped:
        classification = classify_release(candidate.title + ' ' + ' '.join(a.subject for a in candidate.articles))
        release = Release(
            subject=candidate.articles[0].subject,
            title=candidate.title,
            group_name=group.name,
            size_bytes=sum(a.bytes for a in candidate.articles),
            completion=candidate.completion,
            classification_score=classification.score,
            accepted=classification.accepted,
            reasons=','.join(classification.reasons),
        )
        db.add(release)
        db.flush()

        file_name = parse_subject(candidate.articles[0].subject).filename
        release_file = ReleaseFile(
            release_id=release.id,
            name=file_name,
            size_bytes=sum(a.bytes for a in candidate.articles),
        )
        db.add(release_file)
        db.flush()

        for article in candidate.articles:
            parsed = parse_subject(article.subject)
            exists = db.scalar(select(UsenetArticle.id).where(UsenetArticle.message_id == article.message_id))
            if exists:
                continue
            db.add(UsenetArticle(
                release_id=release.id,
                release_file_id=release_file.id,
                group_name=group.name,
                article_number=article.article_number,
                message_id=article.message_id,
                subject=article.subject,
                bytes=article.bytes,
                segment=parsed.segment,
                segment_total=parsed.segment_total,
            ))
        release_count += 1
        accepted_count += int(classification.accepted)

    group.high_water = max(row['article_number'] for row in rows)
    db.commit()
    return {
        'articles': len(rows),
        'releases': release_count,
        'accepted': accepted_count,
        'high_water': group.high_water,
        'server_high': server_high,
    }
