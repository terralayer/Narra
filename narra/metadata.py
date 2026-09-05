from dataclasses import dataclass
import re


@dataclass(slots=True)
class ParsedBookMetadata:
    title: str
    author: str | None = None
    series: str | None = None
    series_number: str | None = None
    narrator: str | None = None
    abridged: bool | None = None
    codec: str | None = None


def _clean(value: str) -> str:
    value = re.sub(r'\b(?:yEnc|audiobook)\b', ' ', value, flags=re.I)
    value = re.sub(r'\.(?:m4b|mp3|m4a|aac|flac|ogg|rar|7z)\b', ' ', value, flags=re.I)
    value = re.sub(r'\s+', ' ', value)
    return value.strip(' -_.[]()')


def extract_metadata(text: str) -> ParsedBookMetadata:
    raw = text.strip()
    lower = raw.lower()
    codec_match = re.search(r'\b(m4b|mp3|m4a|aac|flac|ogg)\b', lower)
    narrator_match = re.search(r'(?:narrated\s+by|narrator)\s*[:\-]?\s*([^\[\]()]+)', raw, re.I)
    series_match = re.search(r'\[([^\]]+?)\s+(?:book|vol(?:ume)?\.?)\s*#?([\d.]+)\]', raw, re.I)
    if not series_match:
        series_match = re.search(r'\b([^\-\[\]]+?)\s+(?:book|vol(?:ume)?\.?)\s*#?([\d.]+)\b', raw, re.I)

    scrubbed = re.sub(r'\[[^\]]+\]', ' ', raw)
    scrubbed = re.sub(r'\([^)]*\)', ' ', scrubbed)
    scrubbed = _clean(scrubbed)
    parts = [p.strip() for p in re.split(r'\s+-\s+', scrubbed) if p.strip()]
    author = parts[0] if len(parts) >= 2 else None
    title = parts[1] if len(parts) >= 2 else (parts[0] if parts else _clean(raw))

    abridged = None
    if 'unabridged' in lower:
        abridged = False
    elif re.search(r'\babridged\b', lower):
        abridged = True

    return ParsedBookMetadata(
        title=title or _clean(raw),
        author=author,
        series=_clean(series_match.group(1)) if series_match else None,
        series_number=series_match.group(2) if series_match else None,
        narrator=_clean(narrator_match.group(1)) if narrator_match else None,
        abridged=abridged,
        codec=codec_match.group(1).upper() if codec_match else None,
    )
