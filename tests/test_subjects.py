from narra.subjects import parse_subject


def test_parse_segment_and_filename():
    parsed = parse_subject('[12/40] "Mistborn.m4b" yEnc (1/10)')
    assert parsed.segment == 12
    assert parsed.segment_total == 40
    assert parsed.filename == 'Mistborn.m4b'


def test_parse_plain_subject():
    parsed = parse_subject('Author - Book Title - 01.mp3')
    assert parsed.filename == 'Author - Book Title - 01.mp3'
