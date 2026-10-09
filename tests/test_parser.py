from datetime import datetime

from logalyzer.parser import parse_file, parse_line


def test_parse_valid_line():
    entry = parse_line("2026-10-09 13:45:02 ERROR [auth] Login failed for user 'admin'")
    assert entry is not None
    assert entry.timestamp == datetime(2026, 10, 9, 13, 45, 2)
    assert entry.level == "ERROR"
    assert entry.source == "auth"
    assert entry.message == "Login failed for user 'admin'"


def test_parse_line_with_extra_spaces():
    entry = parse_line("2026-10-09 13:45:02   INFO   [api]   all good")
    assert entry is not None
    assert entry.level == "INFO"
    assert entry.message == "all good"


def test_parse_malformed_line_returns_none():
    assert parse_line("this line has no structure") is None
    assert parse_line("2026-10-09 13:45:02 BOGUS [x] bad level") is None
    assert parse_line("2026-13-99 99:99:99 INFO [x] bad date") is None


def test_parse_blank_line_returns_none():
    assert parse_line("") is None
    assert parse_line("   \n") is None


def test_parse_file_counts_skipped(tmp_path):
    log = tmp_path / "test.log"
    log.write_text(
        "2026-10-09 10:00:00 INFO [api] ok\n"
        "broken line here\n"
        "2026-10-09 10:01:00 ERROR [db] boom\n"
    )
    entries, skipped = parse_file(str(log))
    assert len(entries) == 2
    assert skipped == 1
    assert entries[1].level == "ERROR"
