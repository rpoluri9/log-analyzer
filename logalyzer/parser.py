"""Parse log lines into structured entries using regular expressions.

Expected log line format:
    2026-10-09 13:45:02 ERROR [auth] Login failed for user 'admin'

Malformed lines are skipped, never crash the tool.
"""
import re
from dataclasses import dataclass
from datetime import datetime

LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r"\s+(?P<level>INFO|WARNING|ERROR|DEBUG|CRITICAL)"
    r"\s+\[(?P<source>[^\]]+)\]"
    r"\s+(?P<message>.*)$"
)

VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    source: str
    message: str
    raw: str


def parse_line(line: str) -> LogEntry | None:
    """Parse one log line. Returns None for blank or malformed lines."""
    line = line.rstrip("\n")
    if not line.strip():
        return None
    match = LOG_LINE_RE.match(line)
    if not match:
        return None
    try:
        ts = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return LogEntry(
        timestamp=ts,
        level=match.group("level"),
        source=match.group("source"),
        message=match.group("message"),
        raw=line,
    )


def parse_file(path: str) -> tuple[list[LogEntry], int]:
    """Parse a whole log file. Returns (entries, skipped_line_count)."""
    entries: list[LogEntry] = []
    skipped = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = parse_line(line)
            if entry is None:
                skipped += 1
            else:
                entries.append(entry)
    return entries, skipped
