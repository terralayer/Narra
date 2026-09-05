from fastapi.testclient import TestClient
from narra.app import app


def test_caps_is_public():
    with TestClient(app) as client:
        response = client.get('/api?t=caps')
    assert response.status_code == 200
    assert b'Audiobook' in response.content


def test_search_requires_key():
    with TestClient(app) as client:
        response = client.get('/api?t=search&q=book')
    assert response.status_code == 401


def test_search_accepts_dev_key():
    with TestClient(app) as client:
        response = client.get('/api?t=search&q=book&apikey=narra-dev-key')
    assert response.status_code == 200
    assert b'<rss' in response.content
