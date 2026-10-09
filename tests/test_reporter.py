from logalyzer.analyzer import summarize
from logalyzer.parser import LogEntry
from logalyzer.reporter import html_report, text_report
from datetime import datetime


def sample_summary():
    entries = [
        LogEntry(datetime(2026, 10, 9, 10, 0), "INFO", "api", "ok", ""),
        LogEntry(datetime(2026, 10, 9, 10, 5), "ERROR", "db", "timeout after 30s", ""),
        LogEntry(datetime(2026, 10, 9, 10, 6), "ERROR", "db", "timeout after 45s", ""),
    ]
    return summarize(entries)


def test_text_report_contents():
    report = text_report(sample_summary(), source="app.log")
    assert "LOG ANALYSIS REPORT" in report
    assert "Total entries: 3" in report
    assert "ERROR" in report
    assert "timeout after #s" in report  # grouped
    assert "2" in report  # count of grouped error
    assert "2026-10-09 10:00" in report  # timeline bucket
    assert "app.log" in report


def test_text_report_no_errors():
    entries = [LogEntry(datetime(2026, 10, 9, 10, 0), "INFO", "api", "ok", "")]
    report = text_report(summarize(entries))
    assert "(none)" in report


def test_html_report_contents():
    report = html_report(sample_summary(), source="app.log")
    assert "<html>" in report
    assert "Log Analysis Report" in report
    assert "Total entries: 3" in report
    assert "timeout after #s" in report
    assert "<table>" in report


def test_html_escapes_content():
    entries = [
        LogEntry(datetime(2026, 10, 9, 10, 0), "ERROR", "api",
                 "<script>alert(1)</script>", "")
    ]
    report = html_report(summarize(entries))
    assert "<script>" not in report
    assert "&lt;script&gt;" in report
