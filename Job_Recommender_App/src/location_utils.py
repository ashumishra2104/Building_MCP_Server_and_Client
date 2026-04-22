import re

# Maps every known spelling/alias → canonical city name.
# Multi-word aliases MUST stay above single-word ones so longest match wins.
ALIAS_TO_CANONICAL = {
    # ── multi-word (checked first) ──────────────────────────────────────────
    "navi mumbai":          "Navi Mumbai",
    "new delhi":            "Delhi",
    "greater noida":        "Noida",
    "bangalore urban":      "Bengaluru",
    "bengaluru east":       "Bengaluru",
    "south delhi":          "Delhi",
    "north delhi":          "Delhi",
    "lower parel":          "Mumbai",
    "pimpri chinchwad":     "Pune",
    "pimpri-chinchwad":     "Pune",
    # ── single-word ─────────────────────────────────────────────────────────
    "bengaluru":            "Bengaluru",
    "bangalore":            "Bengaluru",
    "gurugram":             "Gurugram",
    "gurgaon":              "Gurugram",
    "delhi":                "Delhi",
    "ncr":                  "Delhi",
    "mumbai":               "Mumbai",
    "bombay":               "Mumbai",
    "goregaon":             "Mumbai",
    "worli":                "Mumbai",
    "churchgate":           "Mumbai",
    "navi":                 "Navi Mumbai",   # "Hybrid - Navi Mumbai" → "navi" alone
    "chennai":              "Chennai",
    "madras":               "Chennai",
    "kolkata":              "Kolkata",
    "calcutta":             "Kolkata",
    "hyderabad":            "Hyderabad",
    "noida":                "Noida",
    "pune":                 "Pune",
    "kharadi":              "Pune",
    "pimpri":               "Pune",
    "ahmedabad":            "Ahmedabad",
    "jaipur":               "Jaipur",
    "coimbatore":           "Coimbatore",
    "lucknow":              "Lucknow",
    "indore":               "Indore",
    "thane":                "Thane",
    "chandigarh":           "Chandigarh",
    "bhopal":               "Bhopal",
    "nagpur":               "Nagpur",
    "kochi":                "Kochi",
    "ernakulam":            "Kochi",
    "vadodara":             "Vadodara",
    "nashik":               "Nashik",
    "varanasi":             "Varanasi",
    "mohali":               "Mohali",
    "raipur":               "Raipur",
    "ranchi":               "Ranchi",
    "mangaluru":            "Mangaluru",
    "mysuru":               "Mysuru",
    "rajkot":               "Rajkot",
    "thiruvananthapuram":   "Thiruvananthapuram",
    "bhubaneswar":          "Bhubaneswar",
    "vijayawada":           "Vijayawada",
    "visakhapatnam":        "Visakhapatnam",
    "vishakhapatnam":       "Visakhapatnam",
    "madurai":              "Madurai",
    "hubli":                "Hubli",
    "belgaum":              "Belgaum",
    "aurangabad":           "Aurangabad",
    "gandhinagar":          "Gandhinagar",
    "kolam":                "Kollam",
    "kollam":               "Kollam",
    "udaipur":              "Udaipur",
    "surat":                "Surat",
    "lucknow":              "Lucknow",
    "ambala":               "Ambala",
    "manesar":              "Gurugram",   # Manesar is in Gurugram district
    "baner":                "Pune",       # Baner is a locality in Pune
}

# Tokens that should never be treated as city names
_IGNORE = frozenset({
    "india", "karnataka", "maharashtra", "telangana", "haryana",
    "uttar pradesh", "tamil nadu", "gujarat", "rajasthan", "west bengal",
    "andhra pradesh", "odisha", "kerala", "punjab", "ladakh",
    "area", "areas", "all", "region", "urban", "metropolitan",
    "greater", "east", "west", "north", "south",
    "hybrid", "remote",
    "district", "division", "city", "suburban", "road", "phase",
    "sector", "stage", "layout", "nagar", "vihar", "yojna",
    "cooperative", "industrial", "estate", "jhandewalan", "mohan",
    "united", "arab", "emirates", "singapore",
    "bengal",   # "West Bengal" splits — block "bengal" alone
})

# Pre-sorted aliases: longest first so multi-word matches beat single-word
_SORTED_ALIASES = sorted(ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)


def _normalize(loc: str) -> str:
    loc = loc.lower()
    loc = re.sub(r'\b(hybrid|remote)\b\s*[-–]\s*', '', loc)  # "Hybrid - X" → "X"
    loc = re.sub(r'\([^)]*\)', '', loc)                       # remove (area codes)
    loc = re.sub(r'\s*/\s*', ', ', loc)                       # "Delhi / NCR" → "Delhi, NCR"
    loc = re.sub(r'\s+', ' ', loc).strip()
    return loc


def location_to_canonicals(location: str) -> set:
    """
    Return all canonical city names contained in a raw location string.
    Handles aliases, multi-city strings, bracket annotations, and hybrid prefixes.
    Self-updating: unknown single-word city tokens are returned as-is (title-cased).
    """
    if not location:
        return set()

    loc = _normalize(location)
    found = set()

    # Pass 1 — known aliases (longest first to avoid sub-word false matches)
    for alias in _SORTED_ALIASES:
        if alias in loc:
            found.add(ALIAS_TO_CANONICAL[alias])

    # Pass 2 — unknown cities: scan each comma-separated segment
    for segment in re.split(r'[,;]', loc):
        segment = segment.strip()
        if not segment:
            continue
        # Skip segment if any alias already matched it
        if any(alias in segment for alias in _SORTED_ALIASES):
            continue
        # Extract words that aren't noise
        words = [
            w for w in segment.split()
            if w not in _IGNORE and len(w) > 2 and not w.isdigit()
        ]
        # Only promote a single clean word to avoid garbage multi-word tokens
        if len(words) == 1:
            found.add(words[0].title())

    return found


def get_available_cities(jobs: list) -> list:
    """
    Scan all loaded jobs and return sorted unique canonical city names.
    Self-updating: new locations in the DB automatically produce new options.
    """
    cities = set()
    for job in jobs:
        cities.update(location_to_canonicals(job.get('location') or ''))
    # Drop garbage: single chars, pure numbers, pure state/country leftovers
    cities = {c for c in cities if len(c) > 2 and not c.isdigit() and c.lower() not in _IGNORE}
    return sorted(cities)


def job_matches_cities(job: dict, selected: list) -> bool:
    """Return True if the job matches any of the selected canonical city names."""
    if not selected:
        return True
    return bool(location_to_canonicals(job.get('location') or '') & set(selected))
