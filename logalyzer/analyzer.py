"""Filter and aggregate parsed log entries."""
import re
from collections import Counter
from datetime import datetime

from .parser import LogEntry

ERROR_LEVELS = ("ERROR", "CRITICAL")
_DIGITS_RE = re.compile(r"\d+")


def normalize_message(message: str) -> str:
    """Replace numbers with '#' so similar errors group together.

    Example: "timeout after 30s" and "timeout after 45s" become one group.
    """
    return _DIGITS_RE.sub("#", message)


def filter_entries(
    entries: list[LogEntry],
    levels: list[str] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[LogEntry]:
    """Keep only entries matching the given levels and/or date range."""
    result = entries
    if levels:
        wanted = {level.upper() for level in levels}
        result = [e for e in result if e.level in wanted]
    if start is not None:
        result = [e for e in result if e.timestamp >= start]
    if end is not None:
        result = [e for e in result if e.timestamp <= end]
    return result


def count_by_level(entries: list[LogEntry]) -> dict[str, int]:
    return dict(Counter(e.level for e in entries))


def top_errors(entries: list[LogEntry], n: int = 5) -> list[tuple[str, int]]:
    """Most common errors, grouped by normalized message."""
    errors = [e for e in entries if e.level in ERROR_LEVELS]
    groups = Counter(normalize_message(e.message) for e in errors)
    return groups.most_common(n)


def timeline(entries: list[LogEntry], bucket: str = "hour") -> dict[str, int]:
    """Count entries per time bucket ('hour' or 'day'), oldest first."""
    buckets: Counter = Counter()
    for e in entries:
        if bucket == "day":
            key = e.timestamp.strftime("%Y-%m-%d")
        else:
            key = e.timestamp.strftime("%Y-%m-%d %H:00")
        buckets[key] += 1
    return dict(sorted(buckets.items()))


def summarize(entries: list[LogEntry], top_n: int = 5) -> dict:
    """Build the full summary dict used by the reporters."""
    return {
        "total": len(entries),
        "by_level": count_by_level(entries),
        "error_count": sum(1 for e in entries if e.level in ERROR_LEVELS),
        "top_errors": top_errors(entries, n=top_n),
        "timeline": timeline(entries),
    }
