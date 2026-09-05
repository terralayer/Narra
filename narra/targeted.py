from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .classifier import classify_release
from .grouping import ArticleRecord, group_articles
from .metadata import extract_metadata
from .models import Author, Book, Edition, NNTPProvider, Narrator, Release, ReleaseFile, Series, UsenetArticle, UsenetGroup
from .nntp import ProviderConfig, probe_yenc_filename, search_overview


SEARCH_HEADERS_PER_GROUP = 50_000


def subject_matches_query(subject: str, query: str) -> bool:
    terms = [term.casefold() for term in query.split() if term.strip()]
    if not terms:
        return False
    haystack = subject.casefold()
    return all(term in haystack for term in terms)


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


def _store_matching_rows(db: Session, config: ProviderConfig, group: UsenetGroup, rows: list[dict]) -> int:
    records = [
        ArticleRecord(
            article_number=row['article_number'],
            message_id=row['message_id'],
            subject=row['subject'],
            bytes=row['bytes'],
        )
        for row in rows
        if row.get('message_id')
    ]
    stored = 0
    for candidate in group_articles(records):
        if any(
            db.scalar(select(UsenetArticle.id).where(UsenetArticle.message_id == article.message_id))
            for article in candidate.articles
        ):
            continue

        classification_text = candidate.title + ' ' + ' '.join(article.subject for article in candidate.articles)
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
            size_bytes=sum(article.bytes for article in candidate.articles),
            completion=candidate.completion,
            classification_score=classification.score,
            accepted=classification.accepted,
            reasons=','.join(dict.fromkeys(classification.reasons)),
            edition_id=edition_id,
        )
        db.add(release)
        db.flush()
        release_file = ReleaseFile(
            release_id=release.id,
            name=detected_name,
            size_bytes=sum(article.bytes for article in candidate.articles),
        )
        db.add(release_file)
        db.flush()
        for article in candidate.articles:
            db.add(UsenetArticle(
                release_id=release.id,
                release_file_id=release_file.id,
                group_name=group.name,
                article_number=article.article_number,
                message_id=article.message_id,
                subject=article.subject,
                bytes=article.bytes,
            ))
        stored += 1
    db.commit()
    return stored


def targeted_search(db: Session, query: str, headers_per_group: int = SEARCH_HEADERS_PER_GROUP) -> int:
    query = query.strip()
    if not query:
        return 0
    provider = db.scalar(
        select(NNTPProvider)
        .where(NNTPProvider.enabled.is_(True))
        .order_by(NNTPProvider.id)
    )
    if not provider:
        return 0

    config = ProviderConfig(
        host=provider.host,
        port=provider.port,
        username=provider.username,
        password=provider.password,
        use_ssl=provider.use_ssl,
    )
    stored = 0
    groups = db.scalars(
        select(UsenetGroup)
        .where(UsenetGroup.enabled.is_(True))
        .order_by(UsenetGroup.name)
    ).all()
    for group in groups:
        try:
            rows = search_overview(config, group.name, query, headers_per_group)
        except Exception:
            db.rollback()
            continue
        if rows:
            stored += _store_matching_rows(db, config, group, rows)
    return stored
