from sqlalchemy import select
from sqlalchemy.orm import Session

from .classifier import classify_release
from .grouping import ArticleRecord, group_articles
from .metadata import extract_metadata
from .models import Author, Book, Edition, NNTPProvider, Narrator, Release, ReleaseFile, Series, UsenetArticle, UsenetGroup
from .nntp import ProviderConfig, probe_yenc_filename, scan_overview
from .subjects import parse_subject


def _get_or_create_named(db: Session, model, name: str | None):
    if not name:
        return None
    existing = db.scalar(select(model).where(model.name == name))
    if existing:
        return existing
    value = model(name=name)
    db.add(value)
    db.flush()
    return value


def _edition_from_subject(db: Session, text: str) -> tuple[str, int | None]:
    meta = extract_metadata(text)
    author = _get_or_create_named(db, Author, meta.author)
    series = _get_or_create_named(db, Series, meta.series)
    narrator = _get_or_create_named(db, Narrator, meta.narrator)

    book = db.scalar(
        select(Book).where(
            Book.title == meta.title,
            Book.author_id == (author.id if author else None),
            Book.series_id == (series.id if series else None),
        )
    )
    if not book:
        book = Book(
            title=meta.title,
            author_id=author.id if author else None,
            series_id=series.id if series else None,
            series_number=meta.series_number,
        )
        db.add(book)
        db.flush()

    edition = Edition(
        book_id=book.id,
        narrator_id=narrator.id if narrator else None,
        abridged=meta.abridged,
        codec=meta.codec,
    )
    db.add(edition)
    db.flush()
    return meta.title, edition.id


def scan_group(db: Session, provider: NNTPProvider, group: UsenetGroup, limit: int = 5000) -> dict:
    saved_high_water = int(group.high_water or 0)
    start = saved_high_water + 1 if saved_high_water > 0 else None
    config = ProviderConfig(
        host=provider.host,
        port=provider.port,
        username=provider.username,
        password=provider.password,
        use_ssl=provider.use_ssl,
    )
    rows, server_high = scan_overview(config, group.name, start, limit)
    if not rows:
        if saved_high_water > 0:
            group.high_water = max(saved_high_water, server_high)
            db.commit()
        return {'articles': 0, 'releases': 0, 'accepted': 0, 'high_water': group.high_water, 'server_high': server_high}

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
        classification_text = candidate.title + ' ' + ' '.join(a.subject for a in candidate.articles)
        classification = classify_release(classification_text)
        detected_name = candidate.title

        if not classification.accepted and 'video-signal' not in classification.reasons and candidate.articles:
            try:
                probed = probe_yenc_filename(config, candidate.articles[0].message_id)
            except Exception:
                probed = None
            if probed:
                detected_name = probed
                probed_classification = classify_release(classification_text + ' ' + probed)
                if probed_classification.score > classification.score:
                    classification = probed_classification
                    classification.reasons.append('yenc-filename')

        title = detected_name
        edition_id = None
        if classification.accepted:
            title, edition_id = _edition_from_subject(db, detected_name)

        release = Release(
            subject=candidate.articles[0].subject,
            title=title,
            group_name=group.name,
            size_bytes=sum(a.bytes for a in candidate.articles),
            completion=candidate.completion,
            classification_score=classification.score,
            accepted=classification.accepted,
            reasons=','.join(dict.fromkeys(classification.reasons)),
            edition_id=edition_id,
        )
        db.add(release)
        db.flush()

        file_name = detected_name or parse_subject(candidate.articles[0].subject).filename
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
