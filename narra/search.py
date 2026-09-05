from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session
from .models import Release


def search_releases(db: Session, query: str = "", *, accepted_only: bool = True, limit: int = 100):
    stmt = select(Release)
    if accepted_only:
        stmt = stmt.where(Release.accepted.is_(True))
    q = query.strip()
    if q:
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            vector = func.to_tsvector("simple", func.coalesce(Release.title, "") + " " + func.coalesce(Release.subject, ""))
            tsquery = func.plainto_tsquery("simple", q)
            stmt = stmt.where(or_(vector.op("@@")(tsquery), func.similarity(Release.title, q) > 0.2))
            stmt = stmt.order_by(func.greatest(func.ts_rank(vector, tsquery), func.similarity(Release.title, q)).desc())
        else:
            pattern = f"%{q}%"
            stmt = stmt.where(or_(Release.title.ilike(pattern), Release.subject.ilike(pattern)))
            stmt = stmt.order_by(Release.id.desc())
    else:
        stmt = stmt.order_by(Release.id.desc())
    return db.scalars(stmt.limit(limit)).all()
