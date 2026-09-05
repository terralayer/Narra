from xml.etree.ElementTree import Element, SubElement, tostring


def build_nzb(*, subject: str, poster: str, group: str, segments: list[dict]) -> bytes:
    nzb = Element('nzb', {'xmlns': 'http://www.newzbin.com/DTD/2003/nzb'})
    file_el = SubElement(nzb, 'file', {'poster': poster or 'unknown', 'date': '0', 'subject': subject})
    groups_el = SubElement(file_el, 'groups')
    SubElement(groups_el, 'group').text = group
    segments_el = SubElement(file_el, 'segments')
    for item in sorted(segments, key=lambda x: int(x.get('number', 0))):
        segment = SubElement(segments_el, 'segment', {
            'bytes': str(int(item.get('bytes', 0))),
            'number': str(int(item.get('number', 0))),
        })
        segment.text = str(item['message_id']).strip('<>')
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(nzb, encoding='utf-8')
