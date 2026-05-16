import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client if credentials exist
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")

# Get the absolute path to the project root for local SQLite fallback
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jobs_repository.db")

def init_db():
    """Initializes local SQLite database for fallback."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # LinkedIn Table V2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linkedin_jobs_v2 (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            posted_at TEXT,
            job_description TEXT,
            search_query TEXT,
            fetched_at DATETIME,
            raw_data TEXT
        )
    ''')

    # Naukri Table V2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS naukri_jobs_v2 (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            posted_at TEXT,
            job_description TEXT,
            search_query TEXT,
            fetched_at DATETIME,
            raw_data TEXT
        )
    ''')

    # Indeed local fallback
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indeed_jobs_local (
            id TEXT PRIMARY KEY,
            position_name TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            posted_at TEXT,
            description TEXT,
            search_query TEXT,
            fetched_at DATETIME,
            raw_data TEXT
        )
    ''')

    # ATS Keywords
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ats_keywords (
            id TEXT PRIMARY KEY,
            user_email TEXT,
            keyword TEXT,
            category TEXT,
            frequency INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            extracted_at DATETIME,
            updated_at DATETIME
        )
    ''')

    conn.commit()
    conn.close()

def save_jobs_to_db(source, search_query, jobs_list):
    """Saves jobs to Supabase (Primary) with SQLite fallback."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if source == "indeed":
        _save_indeed_to_db(jobs_list, search_query, timestamp)
        return

    table_name = "linkedin_jobs_v2" if source == "linkedin" else "naukri_jobs_v2"

    db_records = []
    for job in jobs_list:
        job_id = str(job.get('jobId') or job.get('id') or job.get('url') or job.get('jdURL'))
        if not job_id or job_id == "None": continue

        record = {
            "job_id": job_id,
            "title": job.get('title'),
            "company": job.get('companyName') or job.get('company'),
            "location": job.get('location'),
            "salary": str(job.get('salary') or job.get('salaryRange') or "Not Disclosed"),
            "posted_at": str(job.get('postedAt') or job.get('footerPlaceholderLabel') or job.get('createdDate') or "Recently"),
            "job_description": job.get('jobDescription') or job.get('description') or "",
            "search_query": search_query,
            "fetched_at": timestamp,
            "raw_data": json.dumps(job)
        }
        db_records.append(record)

    # 1. Try Supabase
    if supabase:
        try:
            for record in db_records:
                supabase.table(table_name).upsert(record).execute()
            print(f"Successfully saved {len(db_records)} jobs to Supabase ({source})")
        except Exception as e:
            print(f"Supabase error: {e}. Falling back to SQLite...")

    # 2. Local Fallback (SQLite)
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for r in db_records:
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table_name}
                (job_id, title, company, location, salary, posted_at, job_description, search_query, fetched_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r['job_id'], r['title'], r['company'], r['location'], r['salary'], r['posted_at'], r['job_description'], r['search_query'], r['fetched_at'], r['raw_data']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error: {e}")


def _save_indeed_to_db(jobs_list, search_query, timestamp):
    """Indeed-specific save — maps all Indeed API fields to the indeed_jobs table."""
    db_records = []
    for job in jobs_list:
        job_id = str(job.get('id') or '')
        if not job_id or job_id == "None":
            continue

        si = job.get('searchInput') or {}
        record = {
            "id":                   job_id,
            "position_name":        job.get('positionName'),
            "company":              job.get('company'),
            "company_indeed_url":   job.get('companyIndeedUrl'),
            "location":             job.get('location'),
            "job_type":             json.dumps(job.get('jobType') or []),
            "salary":               str(job.get('salary')) if job.get('salary') else None,
            "rating":               job.get('rating'),
            "reviews_count":        job.get('reviewsCount'),
            "posted_at":            job.get('postedAt'),
            "posting_date_parsed":  job.get('postingDateParsed'),
            "description":          job.get('description'),
            "description_html":     job.get('descriptionHTML'),
            "url":                  job.get('url'),
            "external_apply_link":  job.get('externalApplyLink'),
            "url_input":            job.get('urlInput'),
            "is_expired":           job.get('isExpired', False),
            "search_position":      si.get('position') or search_query,
            "search_location":      si.get('location'),
            "search_country":       si.get('country'),
            "scraped_at":           job.get('scrapedAt'),
            "fetched_at":           timestamp,
            "raw_data":             job,
        }
        db_records.append(record)

    # 1. Supabase
    if supabase:
        try:
            for record in db_records:
                supabase.table("indeed_jobs").upsert(record).execute()
            print(f"Saved {len(db_records)} Indeed jobs to Supabase")
        except Exception as e:
            print(f"Supabase error (indeed): {e}")

    # 2. SQLite fallback (simplified)
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for r in db_records:
            cursor.execute('''
                INSERT OR REPLACE INTO indeed_jobs_local
                (id, position_name, company, location, salary, posted_at, description, search_query, fetched_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r['id'], r['position_name'], r['company'], r['location'], r['salary'],
                  r['posted_at'], r['description'], r.get('search_position'), r['fetched_at'],
                  json.dumps(r['raw_data'])))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error (indeed): {e}")

def get_jobs_from_db(source, search_query=None, limit=100):
    """Fetch jobs from Supabase (primary) or SQLite fallback."""
    if source == "indeed":
        return _get_indeed_from_db(search_query, limit)

    table_name = "linkedin_jobs_v2" if source == "linkedin" else "naukri_jobs_v2"

    if supabase:
        try:
            query = supabase.table(table_name).select("*")
            if search_query:
                query = query.ilike("title", f"%{search_query}%")
            result = query.limit(limit).order("fetched_at", desc=True).execute()
            jobs = []
            for row in result.data:
                job = json.loads(row["raw_data"])
                job["_fetched_at"] = row.get("fetched_at", "")
                jobs.append(job)
            return jobs
        except Exception as e:
            print(f"Supabase fetch error: {e}")

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_query:
        cursor.execute(
            f"SELECT raw_data FROM {table_name} WHERE title LIKE ? ORDER BY fetched_at DESC LIMIT ?",
            (f"%{search_query}%", limit),
        )
    else:
        cursor.execute(
            f"SELECT raw_data FROM {table_name} ORDER BY fetched_at DESC LIMIT ?",
            (limit,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def _get_indeed_from_db(search_query=None, limit=100):
    """Fetch Indeed jobs — raw_data is JSONB in Supabase (returns dict, not string)."""
    if supabase:
        try:
            query = supabase.table("indeed_jobs").select("*")
            if search_query:
                query = query.ilike("position_name", f"%{search_query}%")
            result = query.limit(limit).order("fetched_at", desc=True).execute()
            jobs = []
            for row in result.data:
                raw = row.get("raw_data")
                if isinstance(raw, dict):
                    job = raw
                elif raw:
                    job = json.loads(raw)
                else:
                    continue
                job["_fetched_at"] = row.get("fetched_at", "")
                jobs.append(job)
            return jobs
        except Exception as e:
            print(f"Supabase fetch error (indeed): {e}")

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_query:
        cursor.execute(
            "SELECT raw_data FROM indeed_jobs_local WHERE position_name LIKE ? ORDER BY fetched_at DESC LIMIT ?",
            (f"%{search_query}%", limit),
        )
    else:
        cursor.execute(
            "SELECT raw_data FROM indeed_jobs_local ORDER BY fetched_at DESC LIMIT ?",
            (limit,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def get_linkedin_posts_from_db(search_query=None, limit=200):
    """Fetch LinkedIn hiring posts from Supabase, ordered by most recent."""
    if supabase:
        try:
            query = supabase.table("linkedin_posts").select("*")
            if search_query:
                query = query.ilike("text", f"%{search_query}%")
            result = query.limit(limit).order("posted_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase fetch error (linkedin_posts): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if search_query:
            cursor.execute(
                "SELECT urn, author_name, author_headline, author_profile_url, text, url, posted_at, time_since_posted, hashtag_source FROM indeed_jobs_local WHERE text LIKE ? ORDER BY posted_at DESC LIMIT ?",
                (f"%{search_query}%", limit),
            )
        else:
            cursor.execute(
                "SELECT urn, author_name, author_headline, author_profile_url, text, url, posted_at, time_since_posted, hashtag_source FROM indeed_jobs_local ORDER BY posted_at DESC LIMIT ?",
                (limit,),
            )
        cols = ["urn","author_name","author_headline","author_profile_url","text","url","posted_at","time_since_posted","hashtag_source"]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        print(f"SQLite error (linkedin_posts): {e}")
        return []


def save_linkedin_posts_to_db(posts_list):
    """Save LinkedIn posts to Supabase with 15-day filter and URN dedup."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=15)

    records = []
    seen_urns = set()
    for post in posts_list:
        urn = post.get("urn")
        if not urn or urn in seen_urns:
            continue
        seen_urns.add(urn)

        iso_date = post.get("postedAtISO")
        if iso_date:
            try:
                post_dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
                if post_dt < cutoff:
                    continue
            except Exception:
                pass

        if post.get("isRepost"):
            continue

        records.append({
            "urn":               urn,
            "author_name":       post.get("authorName"),
            "author_headline":   post.get("authorHeadline"),
            "author_profile_url": post.get("authorProfileUrl"),
            "text":              post.get("text"),
            "url":               post.get("url"),
            "posted_at":         iso_date,
            "time_since_posted": post.get("timeSincePosted"),
            "is_repost":         False,
            "author_type":       post.get("authorType"),
            "hashtag_source":    post.get("inputUrl"),
            "scraped_at":        now.isoformat(),
        })

    if not records:
        return 0

    if supabase:
        try:
            supabase.table("linkedin_posts").upsert(records, on_conflict="urn").execute()
            print(f"Saved {len(records)} LinkedIn posts to Supabase")
            return len(records)
        except Exception as e:
            print(f"Supabase error (linkedin_posts save): {e}")
    return 0


def toggle_job_application(user_email, job_id, source):
    """Toggle applied state. Returns True if now applied, False if now unapplied."""
    if not supabase:
        return False
    try:
        existing = (
            supabase.table("job_applications")
            .select("id")
            .eq("user_email", user_email)
            .eq("job_id", str(job_id))
            .eq("source", source)
            .limit(1)
            .execute()
        )
        if existing.data:
            supabase.table("job_applications").delete().eq("id", existing.data[0]["id"]).execute()
            return False
        else:
            from datetime import datetime, timezone
            supabase.table("job_applications").insert({
                "user_email": user_email,
                "job_id":     str(job_id),
                "source":     source,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            return True
    except Exception as e:
        print(f"Error toggling job application: {e}")
        return False


def get_applied_job_ids(user_email):
    """Return set of job_ids the user has marked as applied."""
    if not supabase:
        return set()
    try:
        result = (
            supabase.table("job_applications")
            .select("job_id")
            .eq("user_email", user_email)
            .execute()
        )
        return {row["job_id"] for row in result.data}
    except Exception as e:
        print(f"Error fetching applied jobs: {e}")
        return set()


def save_user_profile(user_email, profile_name, resume_text, candidate_name, candidate_email, candidate_phone, raw_pdf_name):
    """Save (or replace) the single active profile for a user."""
    if not supabase:
        return False
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "user_email":     user_email,
            "profile_name":   profile_name,
            "resume_text":    resume_text,
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "candidate_phone": candidate_phone,
            "raw_pdf_name":   raw_pdf_name,
            "is_active":      True,
            "updated_at":     now,
        }
        # Upsert on user_email — one profile per user
        supabase.table("user_profiles").upsert(record, on_conflict="user_email").execute()
        return True
    except Exception as e:
        print(f"Error saving user profile: {e}")
        return False


def get_active_profile(user_email):
    """Fetch the active profile for a user. Returns dict or None."""
    if not supabase:
        return None
    try:
        result = (
            supabase.table("user_profiles")
            .select("*")
            .eq("user_email", user_email)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


def delete_user_profile(user_email):
    """Delete the active profile for a user."""
    if not supabase:
        return False
    try:
        supabase.table("user_profiles").delete().eq("user_email", user_email).execute()
        return True
    except Exception as e:
        print(f"Error deleting user profile: {e}")
        return False


def get_dashboard_stats(user_email):
    """Fetch all stats needed for the dashboard in one place."""
    if not supabase:
        return None
    try:
        from datetime import datetime, timezone, timedelta
        now     = datetime.now(timezone.utc)
        week_ago = (now - timedelta(days=7)).isoformat()

        # ── Totals in DB ──────────────────────────────────────────
        l_total = supabase.table("linkedin_jobs_v2").select("*", count="exact").limit(1).execute().count or 0
        n_total = supabase.table("naukri_jobs_v2").select("*", count="exact").limit(1).execute().count or 0
        i_total = supabase.table("indeed_jobs").select("*", count="exact").limit(1).execute().count or 0

        # ── New jobs this week ─────────────────────────────────────
        l_new = supabase.table("linkedin_jobs_v2").select("*", count="exact").gte("fetched_at", week_ago).limit(1).execute().count or 0
        n_new = supabase.table("naukri_jobs_v2").select("*", count="exact").gte("fetched_at", week_ago).limit(1).execute().count or 0
        i_new = supabase.table("indeed_jobs").select("*", count="exact").gte("fetched_at", week_ago).limit(1).execute().count or 0

        # ── Applications ───────────────────────────────────────────
        apps = supabase.table("job_applications").select("*").eq("user_email", user_email).execute().data or []

        applied_total   = len(apps)
        applied_this_wk = sum(1 for a in apps if a.get("applied_at","") >= week_ago)
        applied_by_src  = {"linkedin": 0, "naukri": 0, "indeed": 0}
        for a in apps:
            src = a.get("source","")
            if src in applied_by_src:
                applied_by_src[src] += 1

        # ── Day-wise applications ──────────────────────────────────
        from collections import defaultdict
        day_counts = defaultdict(int)
        dow_counts = defaultdict(int)  # 0=Mon..6=Sun
        for a in apps:
            ts = a.get("applied_at","")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
                    day_counts[dt.strftime("%Y-%m-%d")] += 1
                    dow_counts[dt.weekday()] += 1
                except Exception:
                    pass

        # ── Top companies applied to ───────────────────────────────
        l_ids = [a["job_id"] for a in apps if a.get("source") == "linkedin"]
        n_ids = [a["job_id"] for a in apps if a.get("source") == "naukri"]
        i_ids = [a["job_id"] for a in apps if a.get("source") == "indeed"]

        company_counts = defaultdict(int)
        if l_ids:
            rows = supabase.table("linkedin_jobs_v2").select("company").in_("job_id", l_ids).execute().data or []
            for r in rows:
                c = r.get("company") or "Unknown"
                company_counts[c] += 1
        if n_ids:
            rows = supabase.table("naukri_jobs_v2").select("company").in_("job_id", n_ids).execute().data or []
            for r in rows:
                c = r.get("company") or "Unknown"
                company_counts[c] += 1
        if i_ids:
            rows = supabase.table("indeed_jobs").select("company").in_("id", i_ids).execute().data or []
            for r in rows:
                c = r.get("company") or "Unknown"
                company_counts[c] += 1

        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "totals":        {"linkedin": l_total, "naukri": n_total, "indeed": i_total},
            "new_this_week": {"linkedin": l_new,   "naukri": n_new,   "indeed": i_new},
            "applied_total":   applied_total,
            "applied_this_wk": applied_this_wk,
            "applied_by_src":  applied_by_src,
            "day_counts":      dict(day_counts),
            "dow_counts":      dict(dow_counts),
            "top_companies":   top_companies,
        }
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return None


def get_all_keys(source):
    """Utility to see unique keys from local SQLite."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    table = "linkedin_jobs_v2" if source == "linkedin" else "naukri_jobs_v2"
    cursor.execute(f"SELECT raw_data FROM {table} LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    unique_keys = set()
    for row in rows:
        data = json.loads(row[0])
        unique_keys.update(data.keys())
    return sorted(list(unique_keys))

# ── ATS Keywords ──────────────────────────────────────────────────────────────

def get_last_extraction_time(user_email):
    """Return ISO timestamp of the last keyword extraction run, or None."""
    if supabase:
        try:
            result = (
                supabase.table("ats_keywords")
                .select("extracted_at")
                .eq("user_email", user_email)
                .order("extracted_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["extracted_at"]
        except Exception as e:
            print(f"Error fetching last extraction time: {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(extracted_at) FROM ats_keywords WHERE user_email = ?",
            (user_email,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        print(f"SQLite error (last extraction time): {e}")
        return None


def save_ats_keywords(user_email, keywords_by_category):
    """
    Bulk upsert extracted keywords. keywords_by_category is:
      {category: {keyword: frequency}}
    On re-extract: increments frequency for pending rows; leaves approved/rejected untouched.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    # Build records — fetch existing statuses first to preserve approved/rejected
    existing = {}
    try:
        if supabase:
            res = supabase.table("ats_keywords").select("id,status,frequency").eq("user_email", user_email).execute()
            for row in res.data or []:
                existing[row["id"]] = row
    except Exception:
        pass

    records = []
    for category, kw_freq in keywords_by_category.items():
        for keyword, frequency in kw_freq.items():
            row_id = f"{user_email}|{keyword}"
            existing_row = existing.get(row_id)
            if existing_row and existing_row["status"] in ("approved", "rejected"):
                # Increment frequency but don't reset status
                records.append({
                    "id": row_id,
                    "user_email": user_email,
                    "keyword": keyword,
                    "category": category,
                    "frequency": existing_row["frequency"] + frequency,
                    "status": existing_row["status"],
                    "extracted_at": now,
                    "updated_at": now,
                })
            else:
                records.append({
                    "id": row_id,
                    "user_email": user_email,
                    "keyword": keyword,
                    "category": category,
                    "frequency": (existing_row["frequency"] + frequency) if existing_row else frequency,
                    "status": "pending",
                    "extracted_at": now,
                    "updated_at": now,
                })

    if not records:
        return 0

    supabase_error = None
    if supabase:
        try:
            supabase.table("ats_keywords").upsert(records, on_conflict="id").execute()
            print(f"Saved {len(records)} ATS keywords to Supabase")
        except Exception as e:
            supabase_error = str(e)
            print(f"Supabase error (ats_keywords save): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for r in records:
            cursor.execute('''
                INSERT OR REPLACE INTO ats_keywords
                (id, user_email, keyword, category, frequency, status, extracted_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (r["id"], r["user_email"], r["keyword"], r["category"],
                  r["frequency"], r["status"], r["extracted_at"], r["updated_at"]))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error (ats_keywords save): {e}")

    return len(records), supabase_error


def get_ats_keywords(user_email, status=None):
    """Fetch ATS keywords for a user, optionally filtered by status."""
    if supabase:
        try:
            query = supabase.table("ats_keywords").select("*").eq("user_email", user_email)
            if status:
                query = query.eq("status", status)
            result = query.order("frequency", desc=True).execute()
            if result.data:          # only trust Supabase if it actually has rows
                return result.data
            # fall through to SQLite if Supabase returned empty (e.g. RLS blocking writes)
        except Exception as e:
            print(f"Supabase error (get_ats_keywords): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT id, user_email, keyword, category, frequency, status, extracted_at, updated_at "
                "FROM ats_keywords WHERE user_email = ? AND status = ? ORDER BY frequency DESC",
                (user_email, status),
            )
        else:
            cursor.execute(
                "SELECT id, user_email, keyword, category, frequency, status, extracted_at, updated_at "
                "FROM ats_keywords WHERE user_email = ? ORDER BY frequency DESC",
                (user_email,),
            )
        cols = ["id", "user_email", "keyword", "category", "frequency", "status", "extracted_at", "updated_at"]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"SQLite error (get_ats_keywords): {e}")
        return []


def update_keyword_status(user_email, keyword, status):
    """Set status of a single keyword (pending | approved | rejected)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    row_id = f"{user_email}|{keyword}"

    if supabase:
        try:
            supabase.table("ats_keywords").update({"status": status, "updated_at": now}).eq("id", row_id).execute()
        except Exception as e:
            print(f"Supabase error (update_keyword_status): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ats_keywords SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, row_id),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error (update_keyword_status): {e}")


def auto_classify_keywords(user_email, min_frequency=5):
    """
    Auto-approve keywords with frequency > min_frequency, reject the rest.
    Returns (approved_count, rejected_count).
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    all_kws = get_ats_keywords(user_email)
    approve_ids = [k["keyword"] for k in all_kws if k["frequency"] > min_frequency]
    reject_ids  = [k["keyword"] for k in all_kws if k["frequency"] <= min_frequency]

    if supabase:
        try:
            if approve_ids:
                supabase.table("ats_keywords").update({"status": "approved", "updated_at": now}) \
                    .eq("user_email", user_email).gt("frequency", min_frequency).execute()
            if reject_ids:
                supabase.table("ats_keywords").update({"status": "rejected", "updated_at": now}) \
                    .eq("user_email", user_email).lte("frequency", min_frequency).execute()
        except Exception as e:
            print(f"Supabase error (auto_classify): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ats_keywords SET status='approved', updated_at=? WHERE user_email=? AND frequency>?",
            (now, user_email, min_frequency),
        )
        cursor.execute(
            "UPDATE ats_keywords SET status='rejected', updated_at=? WHERE user_email=? AND frequency<=?",
            (now, user_email, min_frequency),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error (auto_classify): {e}")

    return len(approve_ids), len(reject_ids)


def bulk_update_keyword_status(user_email, keywords, status):
    """Set status for a list of keyword strings in one shot."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    if not keywords:
        return

    ids = [f"{user_email}|{kw}" for kw in keywords]

    if supabase:
        try:
            supabase.table("ats_keywords").update({"status": status, "updated_at": now}) \
                .in_("id", ids).execute()
        except Exception as e:
            print(f"Supabase error (bulk_update): {e}")

    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany(
            "UPDATE ats_keywords SET status=?, updated_at=? WHERE id=?",
            [(status, now, rid) for rid in ids],
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"SQLite error (bulk_update): {e}")


# Initialize on import
init_db()
