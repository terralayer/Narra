from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import UsenetGroup


DEFAULT_AUDIOBOOK_GROUPS = (
    "alt.binaries.audiobooks",
    "alt.binaries.mp3.audiobooks",
    "alt.binaries.mp3.audiobooks.highspeed",
    "alt.binaries.mp3.audiobooks.repost",
    "alt.binaries.mp3.audiobooks.scifi",
    "alt.binaries.mp3.abooks",
    "alt.binaries.sounds.audiobooks",
    "alt.binaries.sounds.audiobooks.scifi-fantasy",
    "alt.binaries.sounds.mp3.audiobooks",
    "alt.binaries.sound.audiobooks",
    "alt.binaries.sounds.audiobook",
)


def seed_default_groups(db: Session) -> int:
    """Insert missing built-in audiobook groups without modifying existing rows."""
    existing = set(
        db.scalars(
            select(UsenetGroup.name).where(UsenetGroup.name.in_(DEFAULT_AUDIOBOOK_GROUPS))
        ).all()
    )
    missing = [name for name in DEFAULT_AUDIOBOOK_GROUPS if name not in existing]
    if missing:
        db.add_all(
            UsenetGroup(name=name, enabled=True, high_water=0)
            for name in missing
        )
        db.commit()
    return len(missing)
