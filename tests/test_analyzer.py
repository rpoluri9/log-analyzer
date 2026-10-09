from datetime import datetime

from logalyzer.analyzer import (
    count_by_level,
    filter_entries,
    normalize_message,
    summarize,
    timeline,
    top_errors,
)
from logalyzer.parser import LogEntry


def make(level, message="msg", ts="2026-10-09 10:00:00", source="api"):
    return LogEntry(
        timestamp=datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"),
        level=level,
        source=source,
        message=message,
        raw="",
    )


def test_normalize_message_groups_numbers():
    assert normalize_message("timeout after 30s") == normalize_message(
        "timeout after 45s"
    )
    assert normalize_message("Job #12 failed") == "Job ## failed"


def test_filter_by_level():
    entries = [make("INFO"), make("ERROR"), make("WARNING")]
    assert len(filter_entries(entries, levels=["ERROR"])) == 1
    assert len(filter_entries(entries, levels=["error", "warning"])) == 2


def test_filter_by_date_range():
    entries = [
        make("INFO", ts="2026-10-08 10:00:00"),
        make("INFO", ts="2026-10-09 10:00:00"),
        make("INFO", ts="2026-10-10 10:00:00"),
    ]
    kept = filter_entries(
        entries,
        start=datetime(2026, 10, 9),
        end=datetime(2026, 10, 9, 23, 59, 59),
    )
    assert len(kept) == 1
    assert kept[0].timestamp.day == 9


def test_count_by_level():
    entries = [make("INFO"), make("INFO"), make("ERROR")]
    assert count_by_level(entries) == {"INFO": 2, "ERROR": 1}


def test_top_errors_groups_similar():
    entries = [
        make("ERROR", "timeout after 30s"),
        make("ERROR", "timeout after 45s"),
        make("ERROR", "disk full"),
        make("INFO", "timeout after 10s"),  # not an error, ignored
    ]
    top = top_errors(entries, n=5)
    assert top[0] == ("timeout after #s", 2)
    assert ("disk full", 1) in top


def test_timeline_buckets_by_hour():
    entries = [
        make("INFO", ts="2026-10-09 10:05:00"),
        make("INFO", ts="2026-10-09 10:50:00"),
        make("INFO", ts="2026-10-09 11:05:00"),
    ]
    tl = timeline(entries)
    assert tl == {"2026-10-09 10:00": 2, "2026-10-09 11:00": 1}


def test_summarize_structure():
    entries = [make("INFO"), make("ERROR", "boom")]
    s = summarize(entries)
    assert s["total"] == 2
    assert s["error_count"] == 1
    assert s["by_level"] == {"INFO": 1, "ERROR": 1}
    assert len(s["top_errors"]) == 1
    assert s["timeline"]
