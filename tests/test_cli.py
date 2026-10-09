import threading
import time

from click.testing import CliRunner

from logalyzer.cli import cli, watch_log

LOG_TEXT = """2026-10-09 10:00:00 INFO [api] all good
2026-10-09 10:01:00 ERROR [db] timeout after 30s
2026-10-09 10:02:00 WARNING [api] slow request
2026-10-09 10:03:00 CRITICAL [db] disk full
broken line
"""


def make_log(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text(LOG_TEXT)
    return str(p)


def test_analyze_text_report(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--log", make_log(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "LOG ANALYSIS REPORT" in result.output
    assert "Total entries: 4" in result.output
    assert "malformed lines skipped" in result.output


def test_analyze_level_filter(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["analyze", "--log", make_log(tmp_path), "--level", "ERROR"]
    )
    assert result.exit_code == 0, result.output
    assert "Total entries: 1" in result.output


def test_analyze_date_filter(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["analyze", "--log", make_log(tmp_path),
              "--start", "2026-10-09 10:02:00"]
    )
    assert result.exit_code == 0, result.output
    assert "Total entries: 2" in result.output


def test_analyze_bad_datetime_fails(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["analyze", "--log", make_log(tmp_path), "--start", "not-a-date"]
    )
    assert result.exit_code != 0


def test_analyze_html_output_file(tmp_path):
    runner = CliRunner()
    out = str(tmp_path / "report.html")
    result = runner.invoke(
        cli, ["analyze", "--log", make_log(tmp_path),
              "--format", "html", "--output", out]
    )
    assert result.exit_code == 0, result.output
    html = (tmp_path / "report.html").read_text()
    assert "<html>" in html
    assert "Total entries: 4" in html


def test_analyze_missing_log_file_fails():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--log", "/nope/missing.log"])
    assert result.exit_code != 0


def test_email_missing_config_fails(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["email", "--log", make_log(tmp_path),
              "--config", str(tmp_path / "nope.json")]
    )
    assert result.exit_code != 0
    assert "Config file not found" in result.output


def test_email_sends_report(tmp_path, monkeypatch):
    import logalyzer.cli as cli_mod

    cfg = tmp_path / "config.json"
    cfg.write_text(
        '{"smtp_host": "x", "smtp_port": 25, "from_addr": "a@b.c", '
        '"to_addrs": ["t@e.st"]}'
    )
    calls = {}

    def fake_send(config, subject, body_text, body_html=None):
        calls["subject"] = subject
        calls["body"] = body_text
        to = config["to_addrs"]
        return to if isinstance(to, list) else [to]

    monkeypatch.setattr(cli_mod, "send_report", fake_send)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["email", "--log", make_log(tmp_path),
              "--config", str(cfg), "--to", "other@e.st"]
    )
    assert result.exit_code == 0, result.output
    assert "other@e.st" in result.output
    assert "LOG ANALYSIS REPORT" in calls["body"]


def test_watch_log_calls_back_on_new_lines(tmp_path):
    p = tmp_path / "watch.log"
    p.write_text("2026-10-09 10:00:00 INFO [api] start\n")
    seen = []

    def writer():
        time.sleep(0.3)
        with open(p, "a") as f:
            f.write("2026-10-09 10:01:00 ERROR [db] boom\n")
            f.write("2026-10-09 10:02:00 INFO [api] ok\n")

    t = threading.Thread(target=writer)
    t.start()
    watch_log(str(p), seen.append, poll_interval=0.05, stop_after=2)
    t.join()
    assert len(seen) == 2
    assert seen[0].level == "ERROR"
    assert seen[0].message == "boom"
