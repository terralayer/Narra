from narra.classifier import classify_release


def test_accepts_audiobook_release():
    result = classify_release('Brandon Sanderson - Mistborn [Unabridged] [M4B]')
    assert result.accepted is True
    assert result.score >= 60
    assert 'audio-format' in result.reasons


def test_rejects_video_release():
    result = classify_release('Movie.Title.2026.1080p.BluRay.x264')
    assert result.accepted is False
    assert 'video-signal' in result.reasons
