from fastapi.testclient import TestClient
from narra.app import app

client = TestClient(app)


def test_caps_is_public():
    response = client.get('/api?t=caps')
    assert response.status_code == 200
    assert b'Audiobook' in response.content


def test_search_requires_key():
    response = client.get('/api?t=search&q=book')
    assert response.status_code == 401


def test_search_accepts_dev_key():
    response = client.get('/api?t=search&q=book&apikey=narra-dev-key')
    assert response.status_code == 200
    assert b'<rss' in response.content
