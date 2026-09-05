from xml.etree import ElementTree as ET
from narra.nzb import build_nzb


def test_builds_valid_nzb_with_message_ids():
    payload = build_nzb(subject='Book', poster='poster', group='alt.binaries.audiobooks', segments=[
        {'number': 2, 'bytes': 20, 'message_id': '<two@example>'},
        {'number': 1, 'bytes': 10, 'message_id': '<one@example>'},
    ])
    root = ET.fromstring(payload)
    ns = {'n': 'http://www.newzbin.com/DTD/2003/nzb'}
    segments = root.findall('.//n:segment', ns)
    assert [s.text for s in segments] == ['one@example', 'two@example']
    assert [s.attrib['number'] for s in segments] == ['1', '2']
