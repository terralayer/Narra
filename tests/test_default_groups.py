from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from narra.db import Base
from narra.models import UsenetGroup
from narra.seed import DEFAULT_AUDIOBOOK_GROUPS, seed_default_groups


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_seeds_all_default_audiobook_groups():
    with make_session() as db:
        seed_default_groups(db)
        names = set(db.scalars(select(UsenetGroup.name)).all())
        assert names == set(DEFAULT_AUDIOBOOK_GROUPS)
        assert len(names) == len(DEFAULT_AUDIOBOOK_GROUPS)


def test_seed_is_idempotent_and_preserves_existing_settings():
    with make_session() as db:
        existing_name = DEFAULT_AUDIOBOOK_GROUPS[0]
        db.add(UsenetGroup(name=existing_name, enabled=False, high_water=12345))
        db.commit()

        seed_default_groups(db)
        seed_default_groups(db)

        groups = db.scalars(select(UsenetGroup).order_by(UsenetGroup.name)).all()
        assert len(groups) == len(DEFAULT_AUDIOBOOK_GROUPS)

        existing = db.scalar(select(UsenetGroup).where(UsenetGroup.name == existing_name))
        assert existing is not None
        assert existing.enabled is False
        assert existing.high_water == 12345

        for group in groups:
            if group.name != existing_name:
                assert group.enabled is True
                assert group.high_water == 0
