"""
One-off script: fetch LinkedIn jobs for 3 PM titles and save to DB.
Run from the project root: python scripts/backfill_linkedin.py
"""
import os
import sys
from dotenv import load_dotenv
from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(override=True)

# Import DB after load_dotenv so Supabase credentials are available
from src.database import init_db, save_jobs_to_db

init_db()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
client = ApifyClient(APIFY_API_TOKEN)

TITLES = [
    "Senior Product Manager",
    "Technical Product Manager",
    "Product Manager",
]

LOCATION = "India"
ROWS = 100


def fetch_and_save(title: str):
    print(f"\n[→] Fetching: {title} ...")
    run_input = {
        "title": title,
        "location": LOCATION,
        "rows": ROWS,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }
    try:
        run = client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        jobs = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        save_jobs_to_db("linkedin", title, jobs)
        print(f"[✓] Saved {len(jobs)} jobs for '{title}'")
        return len(jobs)
    except ApifyApiError as e:
        print(f"[✗] Apify error for '{title}': {e}")
        return 0
    except Exception as e:
        print(f"[✗] Unexpected error for '{title}': {e}")
        return 0


if __name__ == "__main__":
    total = 0
    for t in TITLES:
        total += fetch_and_save(t)
    print(f"\nDone. Total jobs fetched & saved: {total}")
