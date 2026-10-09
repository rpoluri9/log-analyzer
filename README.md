# logalyzer — DevOps Log Analyzer CLI Tool

A command-line tool that reads server log files, finds errors, and produces
summary reports — the kind of tool DevOps teams use every day.

## Features

- **Log parsing** — reads log lines with regular expressions
  (timestamp, level, source, message); malformed lines are skipped safely
- **Error analysis** — counts entries by level, groups similar errors together
  (numbers are normalized, so "timeout after 30s" and "timeout after 45s"
  become one group)
- **Filtering** — by log level (`INFO`, `WARNING`, `ERROR`, ...) and by date range
- **Summary reports** — top errors, counts per level, and an hourly timeline,
  in plain text or HTML
- **Email reports** — sends the summary over SMTP using a JSON config file
- **Live watch mode** — like `tail -f`: alerts the moment new errors appear
- **Installable** — ships as a real `logalyzer` command via `pyproject.toml`

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| CLI        | Click                               |
| Parsing    | Regular expressions (`re`)          |
| Email      | smtplib + email.message             |
| Config     | JSON file                           |
| Tests      | pytest, Click's CliRunner           |
| Packaging  | pyproject.toml (setuptools)         |

## Project Structure

```
log-analyzer/
├── logalyzer/
│   ├── __init__.py     # package version
│   ├── cli.py          # Click commands: analyze, email, watch
│   ├── parser.py       # regex log-line parsing -> LogEntry
│   ├── analyzer.py     # filtering, counting, grouping, timeline
│   ├── reporter.py     # text and HTML report builders
│   └── mailer.py       # SMTP email sending
├── tests/              # pytest suite (27 tests)
├── sample_logs/
│   ├── app.log              # realistic sample log (262 lines)
│   └── generate_sample.py   # regenerates the sample log
├── images/             # architecture diagrams
├── config.json         # example SMTP + paths config
├── pyproject.toml      # packaging: installs the `logalyzer` command
└── requirements.txt
```

Expected log line format:

```
2026-10-09 13:45:02 ERROR [auth] Login failed for user 'admin'
```

## Installation

```bash
python -m venv venv && source venv/bin/activate
pip install -e .
```

Verify it works:

```bash
logalyzer --version
```

## Usage

Analyze the sample log and print a text report:

```bash
logalyzer analyze --log sample_logs/app.log
```

Show only errors, top 10:

```bash
logalyzer analyze --log sample_logs/app.log --level ERROR --top 10
```

Filter by date range:

```bash
logalyzer analyze --log sample_logs/app.log --start 2026-10-08 --end 2026-10-09
```

Save an HTML report to a file:

```bash
logalyzer analyze --log sample_logs/app.log --format html --output report.html
```

Watch a log live and alert on new errors (like `tail -f`):

```bash
logalyzer watch --log sample_logs/app.log
```

Email the report (edit `config.json` with your SMTP settings first):

```bash
logalyzer email --log sample_logs/app.log --config config.json
```

## Config File Reference (`config.json`)

| Key          | Meaning                                    |
|--------------|--------------------------------------------|
| `smtp_host`  | SMTP server address (e.g. smtp.gmail.com)  |
| `smtp_port`  | SMTP port (587 for TLS)                    |
| `use_tls`    | `true` to upgrade the connection with TLS  |
| `username`   | SMTP login username (empty for no login)   |
| `password`   | SMTP login password / app password         |
| `from_addr`  | Sender address                             |
| `to_addrs`   | List of recipient addresses                |
| `log_paths`  | Default log files (for your own scripts)   |

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: log-line parsing (valid + malformed lines), error counting and
grouping, level/date filtering, text and HTML report generation, SMTP sending
with a mocked server, CLI commands via Click's test runner, and live
file-watching.

## Design Notes

- **Small modules, one job each**: parsing, analysis, reporting, email, and
  the CLI live in separate files, so each part is easy to test alone.
- **Never crash on bad input**: malformed log lines are counted and skipped;
  a missing Redis-style dependency does not exist — the tool only needs
  the standard library plus Click.
- **Testable by design**: the file-watching loop takes a `stop_after`
  parameter so tests can exercise it without hanging; SMTP is injected
  through a plain dict config so it can be mocked.
- **Numbers normalized for grouping**: error messages have their digits
  replaced before grouping, which surfaces real patterns instead of
  hundreds of one-off lines.

## Possible Extensions

- Support more log formats (Nginx access logs, JSON logs)
- Alert thresholds in watch mode (e.g. page me after 10 errors/minute)
- Slack/Discord notifications next to email
- SQLite storage of past summaries for trend graphs
- `--follow` across rotated log files (`app.log.1`, ...)
