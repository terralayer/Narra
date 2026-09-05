from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import threading

from sqlalchemy import select

from .db import SessionLocal
from .models import NNTPProvider, ScanState, UsenetGroup
from .scanner import scan_group

ALLOWED_INTERVALS = (0, 1, 5, 10, 15, 30, 60)
DEFAULT_INTERVAL_MINUTES = 5
_SETTING_KEY = "__narra_auto_scan_minutes__"


def get_auto_scan_interval(db) -> int:
    row = db.scalar(select(ScanState).where(ScanState.group_name == _SETTING_KEY))
    if row and row.last_article in ALLOWED_INTERVALS:
        return int(row.last_article)
    return DEFAULT_INTERVAL_MINUTES


def set_auto_scan_interval(db, minutes: int) -> int:
    if minutes not in ALLOWED_INTERVALS:
        raise ValueError(f"interval must be one of {ALLOWED_INTERVALS}")
    row = db.scalar(select(ScanState).where(ScanState.group_name == _SETTING_KEY))
    if row:
        row.last_article = minutes
    else:
        db.add(ScanState(group_name=_SETTING_KEY, last_article=minutes))
    db.commit()
    return minutes


@dataclass(slots=True)
class ScanAllSummary:
    groups: int = 0
    articles: int = 0
    releases: int = 0
    accepted: int = 0
    errors: int = 0


def scan_all_enabled(session_factory=SessionLocal) -> ScanAllSummary:
    summary = ScanAllSummary()
    with session_factory() as db:
        provider = db.scalar(
            select(NNTPProvider)
            .where(NNTPProvider.enabled.is_(True))
            .order_by(NNTPProvider.id)
        )
        if not provider:
            return summary
        groups = db.scalars(
            select(UsenetGroup)
            .where(UsenetGroup.enabled.is_(True))
            .order_by(UsenetGroup.name)
        ).all()
        for group in groups:
            try:
                result = scan_group(db, provider, group)
            except Exception:
                db.rollback()
                summary.errors += 1
                continue
            summary.groups += 1
            summary.articles += int(result.get("articles", 0))
            summary.releases += int(result.get("releases", 0))
            summary.accepted += int(result.get("accepted", 0))
    return summary


class AutoScanner:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self._stop = threading.Event()
        self._run_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self.running = False
        self.last_started_at: datetime | None = None
        self.last_finished_at: datetime | None = None
        self.next_scan_at: datetime | None = None
        self.last_summary = ScanAllSummary()
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="narra-auto-scan", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def run_once(self) -> ScanAllSummary | None:
        if not self._run_lock.acquire(blocking=False):
            return None
        try:
            self.running = True
            self.last_started_at = datetime.utcnow()
            self.last_error = None
            try:
                self.last_summary = scan_all_enabled(self.session_factory)
            except Exception as exc:
                self.last_error = str(exc)
            self.last_finished_at = datetime.utcnow()
            return self.last_summary
        finally:
            self.running = False
            self._run_lock.release()

    def _interval(self) -> int:
        with self.session_factory() as db:
            return get_auto_scan_interval(db)

    def _loop(self) -> None:
        first = True
        while not self._stop.is_set():
            interval = self._interval()
            if interval == 0:
                self.next_scan_at = None
                self._stop.wait(5)
                first = False
                continue
            if first:
                self.run_once()
                first = False
            interval = self._interval()
            if interval == 0:
                continue
            self.next_scan_at = datetime.utcnow() + timedelta(minutes=interval)
            if self._stop.wait(interval * 60):
                break
            self.run_once()


auto_scanner = AutoScanner()
