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


def overview_bounds(server_first: int, server_last: int, start: int | None, limit: int) -> tuple[int, int]:
    limit = max(1, int(limit))
    first = int(server_first)
    last = int(server_last)
    if start is None:
        high = last
        low = max(first, high - limit + 1)
        return low, high
    low = max(first, int(start))
    high = min(last, low + limit - 1)
    return low, high


def _overview_row(article_number: int, overview: dict) -> dict:
    return {
        'article_number': int(article_number),
        'subject': decode_subject(overview.get('subject', '')),
        'message_id': overview.get('message-id', '').strip('<>'),
        'bytes': int(overview.get(':bytes', 0) or 0),
        'from': overview.get('from', ''),
        'date': overview.get('date', ''),
    }


def scan_overview(config: ProviderConfig, group: str, start: int | None, limit: int = 5000):
    with connect(config) as client:
        _response, _count, first, last, _name = client.group(group)
        low, high = overview_bounds(int(first), int(last), start, limit)
        if low > high:
            return [], int(last)
        _resp, rows = client.over((low, high))
        return [_overview_row(article_number, overview) for article_number, overview in rows], int(last)


def search_overview(config: ProviderConfig, group: str, query: str, limit: int = 50_000) -> list[dict]:
    """Search a bounded recent header window without advancing group scan state."""
    terms = [term.casefold() for term in query.split() if term.strip()]
    if not terms:
        return []
    with connect(config) as client:
        _response, _count, first, last, _name = client.group(group)
        low, high = overview_bounds(int(first), int(last), None, limit)
        if low > high:
            return []
        _resp, rows = client.over((low, high))
        results = []
        for article_number, overview in rows:
            subject = decode_subject(overview.get('subject', ''))
            folded = subject.casefold()
            if all(term in folded for term in terms):
                row = _overview_row(article_number, overview)
                row['subject'] = subject
                results.append(row)
        return results


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
