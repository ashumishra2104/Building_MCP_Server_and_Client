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
    
    conn.commit()
    conn.close()

def save_jobs_to_db(source, search_query, jobs_list):
    """Saves jobs to Supabase (Primary) with SQLite fallback."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            # Upsert into Supabase
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

def get_jobs_from_db(source, search_query=None, limit=100):
    """Fetch jobs from Supabase (primary) or SQLite fallback."""
    table_name = "linkedin_jobs_v2" if source == "linkedin" else "naukri_jobs_v2"

    if supabase:
        try:
            query = supabase.table(table_name).select("*")
            if search_query:
                query = query.ilike("title", f"%{search_query}%")
            result = query.limit(limit).order("fetched_at", desc=True).execute()
            return [json.loads(row["raw_data"]) for row in result.data]
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

# Initialize on import
init_db()
