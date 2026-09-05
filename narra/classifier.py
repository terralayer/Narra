from dataclasses import dataclass
import re


AUDIO_FORMATS = ("m4b", "mp3", "m4a", "aac", "flac", "ogg")
ARCHIVE_FORMATS = ("rar", "7z")
VIDEO_SIGNALS = ("1080p", "2160p", "720p", "bluray", "webrip", "web-dl", "x264", "x265", "h264", "h265")
BOOK_SIGNALS = ("unabridged", "abridged", "audiobook", "narrated by", "narrator")


@dataclass(slots=True)
class Classification:
    accepted: bool
    score: int
    reasons: list[str]


def _has_token(value: str, token: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", value) is not None


def classify_release(text: str) -> Classification:
    value = text.lower()
    score = 0
    reasons: list[str] = []

    if any(_has_token(value, fmt) for fmt in AUDIO_FORMATS):
        score += 65
        reasons.append("audio-format")
    if any(_has_token(value, fmt) for fmt in ARCHIVE_FORMATS):
        score += 10
        reasons.append("archive")
    if any(signal in value for signal in BOOK_SIGNALS):
        score += 25
        reasons.append("audiobook-signal")
    if re.search(r"\b(book|volume|vol\.?|series)\s*#?\d+\b", value):
        score += 10
        reasons.append("series-signal")
    if any(signal in value for signal in VIDEO_SIGNALS):
        score -= 100
        reasons.append("video-signal")

    return Classification(accepted=score >= 60 and "video-signal" not in reasons, score=score, reasons=reasons)
