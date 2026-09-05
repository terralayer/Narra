from dataclasses import dataclass
import re


@dataclass(slots=True)
class ParsedSubject:
    raw: str
    filename: str
    segment: int | None = None
    segment_total: int | None = None


_SEGMENT = re.compile(r"\[(\d+)/(\d+)\]")
_QUOTED = re.compile(r'"([^"]+)"')
_YENC = re.compile(r"\s+yEnc(?:\s+\(\d+/\d+\))?\s*$", re.I)


def parse_subject(subject: str) -> ParsedSubject:
    segment = segment_total = None
    match = _SEGMENT.search(subject)
    if match:
        segment, segment_total = map(int, match.groups())

    quoted = _QUOTED.search(subject)
    if quoted:
        filename = quoted.group(1).strip()
    else:
        filename = _SEGMENT.sub("", subject)
        filename = _YENC.sub("", filename).strip(" -")

    return ParsedSubject(subject, filename, segment, segment_total)
