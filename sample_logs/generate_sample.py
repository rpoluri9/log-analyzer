#!/usr/bin/env python3
"""Generate a realistic sample log file for trying out logalyzer.

Run:  python sample_logs/generate_sample.py
Writes: sample_logs/app.log
"""
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")

INFO_MESSAGES = [
    ("api", "Request completed GET /api/products 200 in {n}ms"),
    ("api", "Request completed POST /api/orders 201 in {n}ms"),
    ("api", "Request completed GET /api/cart 200 in {n}ms"),
    ("auth", "User '{u}' logged in from {ip}"),
    ("worker", "Job #{n} finished in {n}s"),
    ("cache", "Cache hit ratio {n}% for product listings"),
    ("db", "Checkpoint completed in {n}ms"),
]

WARNING_MESSAGES = [
    ("api", "Slow request: GET /api/products took {n}ms"),
    ("db", "High memory usage: {n}%"),
    ("worker", "Retrying job #{n} (attempt {n})"),
    ("cache", "Cache miss rate above threshold: {n}%"),
    ("auth", "Multiple login attempts for user '{u}' from {ip}"),
]

ERROR_MESSAGES = [
    ("db", "Database connection failed: timeout after {n}s"),
    ("auth", "Login failed for user '{u}' from {ip}"),
    ("api", "Payment gateway error: card declined for order #{n}"),
    ("api", "File not found: /var/www/static/logo{n}.png"),
    ("worker", "Worker crashed: out of memory processing job #{n}"),
    ("db", "Deadlock detected, transaction rolled back"),
]

CRITICAL_MESSAGES = [
    ("db", "Disk full on /var/log, writes disabled"),
    ("api", "Service unavailable: upstream timeout on /api/orders"),
]

USERS = ["admin", "ramesh", "jdoe", "msmith"]
IPS = ["192.168.1.10", "10.0.0.5", "203.0.113.42", "198.51.100.7"]


def fill(template):
    return template.format(
        n=random.randint(2, 900),
        u=random.choice(USERS),
        ip=random.choice(IPS),
    )


def main():
    start = datetime(2026, 10, 7, 8, 0, 0)
    lines = []
    ts = start
    for _ in range(260):
        ts += timedelta(minutes=random.randint(1, 40))
        roll = random.random()
        if roll < 0.62:
            level, source, template = "INFO", *random.choice(INFO_MESSAGES)
        elif roll < 0.78:
            level, source, template = "WARNING", *random.choice(WARNING_MESSAGES)
        elif roll < 0.97:
            level, source, template = "ERROR", *random.choice(ERROR_MESSAGES)
        else:
            level, source, template = "CRITICAL", *random.choice(CRITICAL_MESSAGES)
        lines.append(
            f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {level} [{source}] {fill(template)}"
        )
    # a couple of malformed lines, like real logs have
    lines.insert(50, "this line is broken and has no structure")
    lines.insert(150, "2026-10-08 25:99:99 BOGUS [x] impossible timestamp")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} lines to {OUT}")


if __name__ == "__main__":
    main()
