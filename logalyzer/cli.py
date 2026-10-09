"""Command-line interface for logalyzer (built with Click)."""
import json
import os
import time
from datetime import datetime

import click

from .analyzer import filter_entries, summarize
from .mailer import send_report
from .parser import VALID_LEVELS, parse_file, parse_line


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_dt(value: str | None) -> datetime | None:
    """Accept 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'."""
    if value is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise click.BadParameter(
        f"bad datetime: {value!r} (use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )


def analyze_paths(paths, levels, start, end, top):
    entries = []
    skipped = 0
    for path in paths:
        batch, bad = parse_file(path)
        entries.extend(batch)
        skipped += bad
    entries = filter_entries(entries, levels=levels, start=start, end=end)
    return summarize(entries, top_n=top), skipped


@click.group()
@click.version_option("1.0.0")
def cli():
    """logalyzer - analyze server log files from the command line."""


@cli.command()
@click.option("--log", "logs", multiple=True, required=True,
              help="Log file to analyze (repeatable).")
@click.option("--level", "levels", multiple=True,
              type=click.Choice(VALID_LEVELS, case_sensitive=False),
              help="Only include these levels, e.g. --level ERROR.")
@click.option("--start", default=None,
              help="Start datetime: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.")
@click.option("--end", default=None, help="End datetime.")
@click.option("--top", default=5, show_default=True,
              help="How many top errors to show.")
@click.option("--format", "fmt", type=click.Choice(["text", "html"]),
              default="text", show_default=True, help="Report format.")
@click.option("--output", default=None,
              help="Write report to this file instead of stdout.")
def analyze(logs, levels, start, end, top, fmt, output):
    """Analyze log files and print a summary report."""
    summary, skipped = analyze_paths(
        logs, list(levels) or None, parse_dt(start), parse_dt(end), top
    )
    source = ", ".join(logs)
    if fmt == "html":
        from .reporter import html_report
        report = html_report(summary, source=source)
    else:
        from .reporter import text_report
        report = text_report(summary, source=source)
        if skipped:
            report = f"({skipped} malformed lines skipped)\n" + report
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo(f"Report written to {output}")
    else:
        click.echo(report)


@cli.command()
@click.option("--log", "logs", multiple=True, required=True,
              help="Log file to analyze (repeatable).")
@click.option("--config", default="config.json", show_default=True,
              help="JSON config file with SMTP settings.")
@click.option("--to", "to_addrs", multiple=True,
              help="Recipient email address (repeatable, overrides config).")
@click.option("--level", "levels", multiple=True, default=("ERROR", "CRITICAL"),
              show_default=True, help="Levels to include in the emailed report.")
@click.option("--subject", default="Logalyzer report", show_default=True)
def email(logs, config, to_addrs, levels, subject):
    """Analyze logs and email the summary report."""
    if not os.path.exists(config):
        raise click.ClickException(f"Config file not found: {config}")
    cfg = load_config(config)
    if to_addrs:
        cfg["to_addrs"] = list(to_addrs)
    summary, _ = analyze_paths(logs, list(levels) or None, None, None, top=5)
    source = ", ".join(logs)
    from .reporter import html_report, text_report
    body_text = text_report(summary, source=source)
    body_html = html_report(summary, source=source)
    sent_to = send_report(cfg, subject, body_text, body_html)
    click.echo(f"Report emailed to {', '.join(sent_to)}")


def watch_log(path, callback, poll_interval=1.0, stop_after=None):
    """Tail -f a file, calling callback(entry) for each new parsed line.

    stop_after stops after that many new lines (used by tests).
    """
    seen = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                entry = parse_line(line)
                if entry is not None:
                    callback(entry)
                seen += 1
                if stop_after is not None and seen >= stop_after:
                    return
            else:
                time.sleep(poll_interval)


@cli.command()
@click.option("--log", "log_path", required=True, help="Log file to watch.")
@click.option("--level", "levels", multiple=True, default=("ERROR", "CRITICAL"),
              show_default=True, help="Alert on these levels.")
def watch(log_path, levels):
    """Watch a log file live and alert on new errors (like tail -f)."""
    wanted = {level.upper() for level in levels}
    click.echo(
        f"Watching {log_path} for {', '.join(sorted(wanted))} ... (Ctrl+C to stop)"
    )

    def on_entry(entry):
        if entry.level in wanted:
            click.echo(
                f"ALERT [{entry.level}] {entry.timestamp} "
                f"[{entry.source}] {entry.message}"
            )

    try:
        watch_log(log_path, on_entry)
    except KeyboardInterrupt:
        click.echo("\nStopped.")
