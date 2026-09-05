from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from narra.db import Base
from narra.models import NNTPProvider, Release, UsenetGroup
from narra.scanner import scan_group


def test_scan_persists_high_water_and_accepted_release(monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        provider = NNTPProvider(name='test', host='news.example', port=563, use_ssl=True)
        group = UsenetGroup(name='alt.binaries.audiobooks', high_water=99)
        db.add_all([provider, group])
        db.commit()

        def fake_scan(_config, _group, start, end):
            assert start == 100
            return [
                {'article_number': 100, 'subject': '[1/2] "Author - Book.m4b" yEnc', 'message_id': 'one@example', 'bytes': 10},
                {'article_number': 101, 'subject': '[2/2] "Author - Book.m4b" yEnc', 'message_id': 'two@example', 'bytes': 20},
            ], 1000

        monkeypatch.setattr('narra.scanner.scan_overview', fake_scan)
        result = scan_group(db, provider, group, limit=10)

        assert result['high_water'] == 101
        assert result['accepted'] == 1
        release = db.scalar(select(Release))
        assert release is not None
        assert release.accepted is True
        assert release.completion == 1.0
