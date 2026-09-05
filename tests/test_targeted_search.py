from types import SimpleNamespace

from fastapi.testclient import TestClient

from narra.app import app
from narra.targeted import subject_matches_query


def test_subject_matches_all_query_terms_case_insensitively():
    assert subject_matches_query('Hugh Howey - Silo Trilogy - M4B Audiobook', 'silo hugh')
    assert not subject_matches_query('Hugh Howey - Wool - M4B Audiobook', 'silo hugh')


def test_search_triggers_targeted_scan_when_cache_is_empty(monkeypatch):
    calls = []

    monkeypatch.setattr('narra.app.search_releases', lambda db, q, accepted_only=True, limit=100: [])
    monkeypatch.setattr('narra.app.targeted_search', lambda db, q: calls.append(q))

    with TestClient(app) as client:
        response = client.get('/search?q=Silo')

    assert response.status_code == 200
    assert calls == ['Silo']


def test_search_skips_live_scan_when_cached_results_exist(monkeypatch):
    cached = [SimpleNamespace(id=1, title='Silo', group_name='alt.binaries.audiobooks', size_bytes=123, completion=1.0)]
    calls = []

    monkeypatch.setattr('narra.app.search_releases', lambda db, q, accepted_only=True, limit=100: cached)
    monkeypatch.setattr('narra.app.targeted_search', lambda db, q: calls.append(q))

    with TestClient(app) as client:
        response = client.get('/search?q=Silo')

    assert response.status_code == 200
    assert b'Silo' in response.content
    assert calls == []
