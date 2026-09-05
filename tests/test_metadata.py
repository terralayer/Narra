from narra.metadata import extract_metadata


def test_extracts_common_audiobook_metadata():
    meta = extract_metadata('Brandon Sanderson - Mistborn [Mistborn Book 1] [Unabridged] [M4B]')
    assert meta.author == 'Brandon Sanderson'
    assert meta.title == 'Mistborn'
    assert meta.series == 'Mistborn'
    assert meta.series_number == '1'
    assert meta.abridged is False
    assert meta.codec == 'M4B'
