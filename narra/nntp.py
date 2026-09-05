from dataclasses import dataclass
from email.header import decode_header, make_header
import nntplib
import re


@dataclass(slots=True)
class ProviderConfig:
    host: str
    port: int = 563
    username: str | None = None
    password: str | None = None
    use_ssl: bool = True
    timeout: int = 30


def connect(config: ProviderConfig):
    cls = nntplib.NNTP_SSL if config.use_ssl else nntplib.NNTP
    return cls(
        config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        readermode=True,
        timeout=config.timeout,
    )


def decode_subject(value: str) -> str:
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def scan_overview(config: ProviderConfig, group: str, start: int, end: int | None = None):
    with connect(config) as client:
        _response, _count, first, last, _name = client.group(group)
        low = max(int(first), int(start))
        high = min(int(last), int(end)) if end is not None else int(last)
        if low > high:
            return [], int(last)
        _resp, rows = client.over((low, high))
        results = []
        for article_number, overview in rows:
            results.append({
                'article_number': int(article_number),
                'subject': decode_subject(overview.get('subject', '')),
                'message_id': overview.get('message-id', '').strip('<>'),
                'bytes': int(overview.get(':bytes', 0) or 0),
                'from': overview.get('from', ''),
                'date': overview.get('date', ''),
            })
        return results, int(last)


def probe_yenc_filename(config: ProviderConfig, message_id: str) -> str | None:
    """Read one article body and return the yEnc name without downloading the payload."""
    with connect(config) as client:
        _response, info = client.body(f'<{message_id.strip("<>")}>')
        for raw_line in info.lines[:25]:
            line = raw_line.decode('latin-1', 'replace') if isinstance(raw_line, bytes) else str(raw_line)
            if line.startswith('=ybegin'):
                match = re.search(r'\bname=(.+)$', line)
                return match.group(1).strip() if match else None
    return None
