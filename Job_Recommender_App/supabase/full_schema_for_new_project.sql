-- ============================================================================
-- Full schema for a brand-new, independent Supabase project running this
-- same Job_Recommender_App codebase.
--
-- HOW TO USE:
--   1. Create a new project at supabase.com
--   2. Open its SQL Editor (left sidebar)
--   3. Paste this entire file, click "Run"
--   4. Copy the new project's URL + service_role (secret) key into this
--      laptop's .env as SUPABASE_URL / SUPABASE_KEY
--
-- NOTE: This is NOT run via the Supabase CLI from this repo — this repo's
-- CLI is already linked to the ORIGINAL Supabase project (see
-- supabase/.temp/linked-project.json). Running `supabase db push` here
-- would target the wrong project. Paste this manually into the new
-- project's SQL Editor instead.
--
-- RLS is left disabled on every table (Postgres default for tables created
-- via raw SQL). This app was built as a single-user personal tool using a
-- service_role key, which bypasses RLS anyway — CLAUDE.md documents a past
-- issue where RLS blocked writes on ats_keywords, so this avoids repeating
-- that. Fine for personal use; NOT fine if you ever expose this to
-- untrusted multi-tenant users.
-- ============================================================================

-- ── LinkedIn jobs ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS linkedin_jobs_v2 (
    job_id             TEXT PRIMARY KEY,
    title              TEXT,
    company            TEXT,
    location           TEXT,
    salary             TEXT,
    posted_at          TEXT,
    job_description    TEXT,
    search_query       TEXT,
    fetched_at         TIMESTAMPTZ,
    raw_data           TEXT,          -- JSON string (json.dumps), NOT jsonb — code does json.loads() on read
    poster_name        TEXT,
    poster_profile_url TEXT
);
ALTER TABLE linkedin_jobs_v2 DISABLE ROW LEVEL SECURITY;

-- ── Naukri jobs (same shape as LinkedIn, no poster columns) ─────────────
CREATE TABLE IF NOT EXISTS naukri_jobs_v2 (
    job_id          TEXT PRIMARY KEY,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    salary          TEXT,
    posted_at       TEXT,
    job_description TEXT,
    search_query    TEXT,
    fetched_at      TIMESTAMPTZ,
    raw_data        TEXT           -- JSON string, NOT jsonb — same as above
);
ALTER TABLE naukri_jobs_v2 DISABLE ROW LEVEL SECURITY;

-- ── Indeed jobs ──────────────────────────────────────────────────────────
-- Wider schema than its SQLite fallback (indeed_jobs_local) since Supabase
-- is primary here and _save_indeed_to_db() writes every one of these fields.
CREATE TABLE IF NOT EXISTS indeed_jobs (
    id                  TEXT PRIMARY KEY,
    position_name       TEXT,
    company             TEXT,
    company_indeed_url  TEXT,
    location            TEXT,
    job_type            TEXT,        -- json.dumps() of a list, stored as text
    salary              TEXT,
    rating              NUMERIC,
    reviews_count        INTEGER,
    posted_at           TEXT,
    posting_date_parsed TEXT,
    description         TEXT,
    description_html    TEXT,
    url                 TEXT,
    external_apply_link TEXT,
    url_input           TEXT,
    is_expired          BOOLEAN,
    search_position     TEXT,
    search_location     TEXT,
    search_country      TEXT,
    scraped_at          TEXT,
    fetched_at          TIMESTAMPTZ,
    raw_data            JSONB        -- genuinely JSONB — code passes the dict directly, no json.dumps/loads
);
ALTER TABLE indeed_jobs DISABLE ROW LEVEL SECURITY;

-- ── LinkedIn hiring posts (hashtag scraper) ──────────────────────────────
CREATE TABLE IF NOT EXISTS linkedin_posts (
    urn                TEXT PRIMARY KEY,
    author_name        TEXT,
    author_headline    TEXT,
    author_profile_url TEXT,
    text               TEXT,
    url                TEXT,
    posted_at          TEXT,
    time_since_posted  TEXT,
    is_repost          BOOLEAN,
    author_type        TEXT,
    hashtag_source     TEXT,
    scraped_at         TEXT
);
ALTER TABLE linkedin_posts DISABLE ROW LEVEL SECURITY;

-- ── Applied-job tracking ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_applications (
    id         BIGSERIAL PRIMARY KEY,
    user_email TEXT,
    job_id     TEXT,
    source     TEXT,
    applied_at TIMESTAMPTZ
);
ALTER TABLE job_applications DISABLE ROW LEVEL SECURITY;

-- ── User profile (resume text, candidate info) ───────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    user_email        TEXT PRIMARY KEY,
    profile_name      TEXT,
    resume_text       TEXT,
    candidate_name    TEXT,
    candidate_email   TEXT,
    candidate_phone   TEXT,
    raw_pdf_name      TEXT,
    candidate_website TEXT,
    candidate_github  TEXT,
    is_active         BOOLEAN,
    updated_at        TIMESTAMPTZ
);
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- ── ATS keyword intelligence ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ats_keywords (
    id           TEXT PRIMARY KEY,       -- format: "{user_email}|{keyword}"
    user_email   TEXT,
    keyword      TEXT,
    category     TEXT,
    frequency    INTEGER DEFAULT 1,
    status       TEXT DEFAULT 'pending', -- pending | approved | rejected
    extracted_at TIMESTAMPTZ,
    updated_at   TIMESTAMPTZ
);
ALTER TABLE ats_keywords DISABLE ROW LEVEL SECURITY;

-- ── Per-user scraper settings ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_settings (
    user_email    TEXT PRIMARY KEY,
    linkedin_rows INTEGER DEFAULT 100,
    naukri_rows   INTEGER DEFAULT 150,
    indeed_rows   INTEGER DEFAULT 75,
    apify_api_key TEXT,
    updated_at    TIMESTAMPTZ
);
ALTER TABLE user_settings DISABLE ROW LEVEL SECURITY;

-- ── STAR Achievement Bank ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS star_achievements (
    id           BIGSERIAL PRIMARY KEY,
    user_email   TEXT NOT NULL,
    company      TEXT NOT NULL,
    project_name TEXT NOT NULL,
    situation    TEXT,
    task         TEXT,
    action       TEXT,
    result       TEXT,
    source_file  TEXT,
    uploaded_at  TIMESTAMPTZ,
    UNIQUE (user_email, company, project_name)
);
ALTER TABLE star_achievements DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Done. All 9 tables the app touches are now created, matching src/database.py
-- exactly (verified against every supabase.table(...) call in that file).
-- ============================================================================
