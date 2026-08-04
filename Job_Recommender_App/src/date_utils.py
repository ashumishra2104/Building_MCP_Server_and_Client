"""Derives a comparable 'posted date' across LinkedIn, Naukri, and Indeed job dicts,
each of which stores posting recency in a different (and differently reliable) shape:

- Indeed:   job['postingDateParsed'] — a real, absolute ISO timestamp.
- Naukri:   job['createdDate']       — a real, absolute timestamp string.
- LinkedIn: job['postedTime']        — only a relative string ("3 days ago"), so it's
            reconstructed against the job's own scrape time (job['_fetched_at']).
"""

import re
from datetime import datetime, timedelta

_RELATIVE_RE = re.compile(r'(\d+)\s*(hour|day|week|month|year)s?\s*ago', re.IGNORECASE)

_UNIT_TO_DAYS = {
    "hour": 1 / 24,
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def _parse_relative(text, reference):
    """Parse strings like '3 days ago' into an absolute datetime offset from
    `reference` (the job's scrape time). Returns None if unparseable."""
    if not text or not reference:
        return None
    text = text.strip()
    if text.lower() in ("just now", "just posted", "today", "recently"):
        return reference
    m = _RELATIVE_RE.search(text)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    return reference - timedelta(days=n * _UNIT_TO_DAYS[unit])


def _parse_timestamp(value):
    """Best-effort parse of the various timestamp string shapes seen across
    Supabase columns and Apify actor output. Returns None if unparseable."""
    if not value or not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_posted_date(job, source):
    """Best-effort absolute posted datetime for a job dict, or None if it can't be
    determined. May be naive or tz-aware depending on source — use days_since_posted()
    to compare across sources safely."""
    if source == "indeed":
        return _parse_timestamp(job.get("postingDateParsed"))
    if source == "naukri":
        return _parse_timestamp(job.get("createdDate"))
    if source == "linkedin":
        fetched_at = _parse_timestamp(job.get("_fetched_at"))
        return _parse_relative(job.get("postedTime"), fetched_at)
    return None


def days_since_posted(job, source):
    """Whole days between now and the job's best-effort posted date, or None if
    unknown. Never negative (clock skew / 'just posted' both floor to 0)."""
    posted = get_posted_date(job, source)
    if posted is None:
        return None
    now = datetime.now(posted.tzinfo) if posted.tzinfo else datetime.now()
    return max(0, (now - posted).days)


def posted_sort_key(job, source, newest_first=True):
    """Sort key that puts unknown-date jobs last regardless of direction, and
    otherwise orders by recency per `newest_first`."""
    d = days_since_posted(job, source)
    if d is None:
        return (1, 0)
    return (0, d) if newest_first else (0, -d)
