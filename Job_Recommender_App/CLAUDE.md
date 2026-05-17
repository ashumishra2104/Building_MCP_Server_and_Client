# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the Streamlit web app (primary entry point)
streamlit run app.py

# Run the MCP server (exposes job search as AI agent tools via FastMCP)
python mcp_server.py

# Install dependencies
pip install -r requirements.txt
```

**WeasyPrint on macOS** requires Homebrew libraries. `src/helper.py` sets `DYLD_LIBRARY_PATH` automatically at import time, but if PDF generation fails locally, ensure `brew install pango` has been run.

## Environment Variables

Create a `.env` file in the project root (already in `.gitignore`):

```
OPENAI_API_KEY=
APIFY_API_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
```

## Architecture

### Entry point & routing

`app.py` is the sole Streamlit entry point. It gates all pages behind a session-state authentication check. Login credentials are hardcoded as `demo@nomail.com` / `password` in `pages/login.py` — this is intentional for the demo.

### Page → module layout

| Page file | Purpose |
|---|---|
| `pages/ai_search.py` | Upload resume → GPT summary/gaps/roadmap → multi-title live Apify job fetch |
| `pages/browse_jobs.py` | Browse cached jobs from DB with filters, pagination, and action tabs |
| `pages/quick_apply.py` | Paste any JD → instantly generate tailored resume, cover letter, or LinkedIn DM |
| `pages/ats_keywords.py` | Extract ATS keywords from all stored JDs, review/approve, auto-inject into resume tailoring |
| `pages/dashboard.py` | Plotly charts over application stats pulled from Supabase |
| `pages/my_profile.py` | Upload resume once, persist to Supabase `user_profiles` table; also hosts ⚙️ Scraper Settings sliders |

### `src/` modules

- **`src/helper.py`** — All OpenAI calls. Uses `gpt-4.1` for resume tailoring and cover letter generation (high-quality, strict rules), `gpt-4o-mini` for lightweight tasks (summarise, extract post signal, generate search titles). Key functions:
  - `generate_search_titles(resume_summary)` — returns `{current_title, search_titles[]}` with current role, aliases (incl. Product Owner variants), one and two levels above. Used by `ai_search.py` to drive multi-title searches.
  - `extract_ats_keywords(jd_texts, progress_callback)` — parallel batch extraction (5 workers, 15 JDs/batch) via `gpt-4.1`. Returns `{category: {keyword: frequency}}`.
  - `tailor_resume(resume_text, job_description, html_template, approved_keywords=None)` — if `approved_keywords` is provided, appends a relevance-filtered injection block; GPT only uses keywords evidenced in the resume.
  - `generate_resume_pdf()` (WeasyPrint) and `generate_linkedin_dm()`.
- **`src/job_api.py`** — Apify actor wrappers for LinkedIn (`BHzefUZlZRKWxkTck`), Naukri (`muhammetakkurtt/naukri-job-scraper`), Indeed (`hMvNSpz3JnHgl5jkh`), and LinkedIn Posts (`Wpp1BZ6yGWjySadk3`). All fetch functions are decorated with `@st.cache_data` and save immediately to DB. The LinkedIn post fetcher starts all 6 hashtag-search runs concurrently then waits for each.
- **`src/database.py`** — Dual-write storage: Supabase is primary, SQLite (`jobs_repository.db`) is the fallback. `init_db()` runs on every import, so SQLite is always bootstrapped. All read functions try Supabase first and fall back to SQLite on failure. ATS keyword functions: `get_last_extraction_time`, `save_ats_keywords`, `get_ats_keywords`, `update_keyword_status`, `auto_classify_keywords`, `bulk_update_keyword_status`. User settings functions: `save_user_settings(user_email, linkedin_rows, naukri_rows, indeed_rows)`, `get_user_settings(user_email)` — upsert/read the `user_settings` table; return defaults `{100, 150, 75}` if no row exists.
- **`src/ui_components.py`** — All card renderers (`render_linkedin_card`, `render_naukri_card`, `render_indeed_card`, `render_linkedin_post_card`) and the shared `_actions_block` helper that renders the "⚡ Actions" expander (Tailor Resume / Cover Letter / Full JD tabs). `_tailor_tab()` auto-fetches approved ATS keywords from DB and passes them to `tailor_resume()`. `JOB_CARD_CSS` is injected by every page that renders cards. `render_linkedin_card` also shows a "👤 Posted by" row (from `posterFullName`/`posterProfileUrl` in the job dict) and a "💬 Message Poster" footer button that links to the poster's LinkedIn profile; falls back to "Poster info not available" when absent.
- **`src/location_utils.py`** — City normalisation: maps raw location strings from all three job sources to canonical city names. The alias table covers Indian cities and common spelling variants. `get_available_cities()` self-updates from loaded jobs.

### MCP server

`mcp_server.py` exposes `get_linkedin_jobs` and `get_naukri_jobs` as FastMCP tools, importing directly from `src/job_api`. Run independently from the Streamlit app — AI agents connect to it as an MCP server.

### Database schema (Supabase tables)

| Table | Key fields |
|---|---|
| `linkedin_jobs_v2` | `job_id` (PK), `title`, `company`, `location`, `salary`, `job_description`, `search_query`, `fetched_at`, `raw_data` (JSON), `poster_name`, `poster_profile_url` |
| `naukri_jobs_v2` | same schema as linkedin (no poster columns) |
| `indeed_jobs` | `id` (PK), `position_name`, `company`, `raw_data` (JSONB — already a dict, not a string) |
| `linkedin_posts` | `urn` (PK), `author_name`, `text`, `url`, `posted_at`, `hashtag_source` |
| `job_applications` | `user_email`, `job_id`, `source`, `applied_at` |
| `user_profiles` | `user_email` (PK/upsert key), one profile per user |
| `ats_keywords` | `id` (PK = `"{user_email}\|{keyword}"`), `user_email`, `keyword`, `category`, `frequency`, `status` (`pending`/`approved`/`rejected`), `extracted_at`, `updated_at` |
| `user_settings` | `user_email` (PK), `linkedin_rows` (default 100), `naukri_rows` (default 150), `indeed_rows` (default 75), `updated_at` |

**Important:** `indeed_jobs.raw_data` is stored as Supabase JSONB (returns a `dict` from the client), unlike LinkedIn/Naukri which store it as a JSON string. `_get_indeed_from_db()` handles both types.

**ATS keywords:** If Supabase returns 0 rows (e.g. RLS blocking writes), `get_ats_keywords()` automatically falls back to SQLite. To fix Supabase writes, disable RLS on the `ats_keywords` table in the Supabase dashboard.

**Poster columns:** `linkedin_jobs_v2.poster_name` and `poster_profile_url` are populated from Apify response fields `posterFullName` / `posterProfileUrl`. `save_jobs_to_db()` includes a Supabase retry guard — if upsert fails (e.g. columns not yet added), it retries without poster fields so existing job saves are never lost. SQLite is migrated via `ALTER TABLE` in `init_db()` on every startup (silently skips if columns already exist).

### Resume tailoring & cover letter pipeline

Both features follow the same flow:
1. Load HTML template (`resume_template.html` or `cover_letter_template.html`) from the project root.
2. Call GPT-4.1 with a strict system prompt — the resume tailoring prompt explicitly forbids inventing experience, upgrading titles, or fabricating metrics.
3. Strip any markdown code fences the LLM may have wrapped around the HTML.
4. Call WeasyPrint to render HTML → PDF, save to disk, offer a `st.download_button`.

### Supabase Edge Functions (cron)

`supabase/functions/` contains two Deno edge functions — `fetch-linkedin-posts` and `save-linkedin-posts` — scheduled daily at 8 AM IST via `supabase/migrations/schedule_linkedin_posts_cron.sql`. The same fetch can be triggered manually from the Posts tab in Browse Jobs.

### Multi-title job search (ai_search.py)

When "Get Job Recommendations" is clicked, `generate_search_titles(resume_summary)` produces an ordered list of 6-8 titles: current role → aliases (incl. Product Owner/Senior Product Owner) → one level above → two levels above → AI variant if applicable.

- **LinkedIn**: top 3 titles, 3 separate Apify actor runs, merged and deduplicated by `jobId → id → url`.
- **Naukri**: all 5 titles joined as a single space-separated keyword string, 1 actor run.
- **Indeed**: top 3 titles, 3 separate actor runs, deduplicated by `id → url`.

Row counts per run are **configurable** via My Profile → ⚙️ Scraper Settings (defaults: LinkedIn 100/call, Naukri 150, Indeed 75/call; loaded from `user_settings` table at fetch time via `get_user_settings()`). Apify hard caps: LinkedIn ~1000, Naukri/Indeed no hard cap.

Dedup key note: raw Apify responses use `jobId` (camelCase), not `job_id` — that is only the SQLite/Supabase column name after saving.

### ATS Keyword Intelligence (pages/ats_keywords.py)

Three-tab page:
- **Extract** — incremental: only JDs fetched after last extraction timestamp are processed. `force_all` checkbox bypasses this. Progress bar shows 4 stages (load → filter → parallel GPT extraction → save).
- **Review** — auto-classify by frequency threshold (approve ≥ N, reject rest), bulk checkbox selection with per-category "Select All", individual approve/reject buttons.
- **My Keywords** — approved keywords shown as chips; auto-injected into every Resume Tailoring call via `_tailor_tab()` in `ui_components.py`.

### Quick Apply page (pages/quick_apply.py)

Standalone page for applying to jobs found outside the portal:

1. Paste any JD into a yellow-tinted text area
2. Choose resume source: saved profile (one-click) or upload a fresh PDF
3. Generate any combination of: tailored resume PDF, cover letter PDF, LinkedIn DM text

- Cover letter auto-extracts company name and job title from the JD via `ask_openai()` (JSON response)
- PDF filenames use `{CandidateName}_Tailored_Resume.pdf` / `{CandidateName}_CoverLetter_{Company}.pdf`
- Reset button clears the JD widget and all generated outputs
- All state uses `qa_` prefix to avoid collisions with browse/search pages

### Browse Jobs filters (pages/browse_jobs.py)

**LinkedIn tab** has an additional "👤 Only show jobs with poster info" toggle. When on, the list is filtered client-side to jobs where `posterFullName` or `posterProfileUrl` is non-empty. The toggle state is included in the pagination signature so the page resets to 1 on toggle. `show_paginated()` accepts an `extra_sig=""` parameter for this purpose.

### Session state conventions

Pages communicate via `st.session_state`. Key names used across pages:

| Key | Set by | Used by |
|---|---|---|
| `authenticated` | login.py | app.py routing |
| `resume_text` | ai_search.py, my_profile.py, browse_jobs.py (auto-load from profile) | all action tabs |
| `candidate_name` | ai_search.py, my_profile.py | card renderers for PDF filenames |
| `active_profile` | browse_jobs.py, my_profile.py | cross-page profile sharing |
| `applied_job_ids` | browse_jobs.py | all card renderers for chip display |
| `db_linkedin_jobs` / `db_naukri_jobs` / `db_indeed_jobs` / `db_linkedin_posts` | browse_jobs.py | pagination and filtering |
| `search_titles` / `linkedin_query` / `naukri_query` / `indeed_query` | ai_search.py | displayed in "Searched:" info banners |
| `ats_all_keywords` / `ats_approved_keywords` / `ats_selected` | ats_keywords.py | ATS review state; cleared on any status change |
| `scraper_settings` | my_profile.py | `{linkedin_rows, naukri_rows, indeed_rows}` loaded from DB; read by ai_search.py at fetch time |
| `qa_resume_text` / `qa_candidate_name` / `qa_resume_source` | quick_apply.py | resume state scoped to Quick Apply |
| `qa_tailored_html` / `qa_cl_html` / `qa_dm_text` | quick_apply.py | generated outputs; cleared on Reset |
