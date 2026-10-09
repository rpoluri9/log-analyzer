"""Build plain-text and HTML summary reports from an analyzer summary."""
from html import escape


def _bar(count: int, width: int = 30) -> str:
    filled = min(count, width)
    return "#" * filled + f" ({count})"


def text_report(summary: dict, title: str = "LOG ANALYSIS REPORT",
                source: str = "") -> str:
    lines = [title, "=" * len(title)]
    if source:
        lines.append(f"Source: {source}")
    lines.append(f"Total entries: {summary['total']}")
    lines.append("")
    lines.append("By level:")
    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        lines.append(f"  {level:<8} {summary['by_level'].get(level, 0)}")
    lines.append("")
    lines.append("Top errors:")
    if summary["top_errors"]:
        for i, (message, count) in enumerate(summary["top_errors"], 1):
            lines.append(f"  {i}. [{count}x] {message}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Timeline (per hour):")
    for bucket, count in summary["timeline"].items():
        lines.append(f"  {bucket}  {_bar(count)}")
    return "\n".join(lines) + "\n"


def html_report(summary: dict, title: str = "Log Analysis Report",
                source: str = "") -> str:
    level_rows = "".join(
        f"<tr><td>{escape(level)}</td>"
        f"<td>{summary['by_level'].get(level, 0)}</td></tr>"
        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    )
    if summary["top_errors"]:
        error_rows = "".join(
            f"<tr><td>{i}</td><td>{escape(message)}</td><td>{count}</td></tr>"
            for i, (message, count) in enumerate(summary["top_errors"], 1)
        )
    else:
        error_rows = '<tr><td colspan="3">No errors found.</td></tr>'
    timeline_rows = "".join(
        f"<tr><td>{escape(bucket)}</td><td>{count}</td></tr>"
        for bucket, count in summary["timeline"].items()
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #202124; }}
h1 {{ color: #1a73e8; }}
table {{ border-collapse: collapse; margin: 12px 0 28px; width: 100%; max-width: 820px; }}
th, td {{ border: 1px solid #dadce0; padding: 8px 12px; text-align: left; }}
th {{ background: #1a73e8; color: white; }}
.meta {{ color: #5f6368; }}
</style>
</head>
<body>
<h1>{escape(title)}</h1>
<p class="meta">Source: {escape(source)} &nbsp;|&nbsp; Total entries: {summary["total"]}</p>
<h2>By level</h2>
<table><tr><th>Level</th><th>Count</th></tr>{level_rows}</table>
<h2>Top errors</h2>
<table><tr><th>#</th><th>Error</th><th>Count</th></tr>{error_rows}</table>
<h2>Timeline (per hour)</h2>
<table><tr><th>Hour</th><th>Entries</th></tr>{timeline_rows}</table>
</body>
</html>
"""
