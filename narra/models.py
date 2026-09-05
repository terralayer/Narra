from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)


class Narrator(Base):
    __tablename__ = "narrators"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)


class Series(Base):
    __tablename__ = "series"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("authors.id"), nullable=True)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id"), nullable=True)
    series_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    author: Mapped[Author | None] = relationship()
    series: Mapped[Series | None] = relationship()


class Edition(Base):
    __tablename__ = "editions"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    narrator_id: Mapped[int | None] = mapped_column(ForeignKey("narrators.id"), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runtime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    abridged: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    asin: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    codec: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bitrate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class UsenetGroup(Base):
    __tablename__ = "usenet_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    high_water: Mapped[int] = mapped_column(Integer, default=0)


class NNTPProvider(Base):
    __tablename__ = "nntp_providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=563)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    max_connections: Mapped[int] = mapped_column(Integer, default=4)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Release(Base):
    __tablename__ = "releases"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(500), index=True)
    group_name: Mapped[str] = mapped_column(String(255), index=True)
    poster: Mapped[str | None] = mapped_column(String(255), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    completion: Mapped[float] = mapped_column(Float, default=0.0)
    classification_score: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reasons: Mapped[str] = mapped_column(Text, default="")
    edition_id: Mapped[int | None] = mapped_column(ForeignKey("editions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReleaseFile(Base):
    __tablename__ = "release_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"), index=True)
    name: Mapped[str] = mapped_column(String(1000))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)


class UsenetArticle(Base):
    __tablename__ = "usenet_articles"
    __table_args__ = (UniqueConstraint("message_id", name="uq_message_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int | None] = mapped_column(ForeignKey("releases.id"), nullable=True, index=True)
    release_file_id: Mapped[int | None] = mapped_column(ForeignKey("release_files.id"), nullable=True, index=True)
    group_name: Mapped[str] = mapped_column(String(255), index=True)
    article_number: Mapped[int] = mapped_column(Integer, index=True)
    message_id: Mapped[str] = mapped_column(String(1000))
    subject: Mapped[str] = mapped_column(Text)
    bytes: Mapped[int] = mapped_column(Integer, default=0)
    segment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segment_total: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MetadataMatch(Base):
    __tablename__ = "metadata_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"), index=True)
    source: Mapped[str] = mapped_column(String(64))
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")


class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ScanState(Base):
    __tablename__ = "scan_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str] = mapped_column(String(255), unique=True)
    last_article: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
