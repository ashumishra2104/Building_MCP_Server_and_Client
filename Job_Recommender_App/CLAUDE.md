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
| `pages/ai_search.py` | Upload resume → GPT summary/gaps/roadmap → live Apify job fetch |
| `pages/browse_jobs.py` | Browse cached jobs from DB with filters, pagination, and action tabs |
| `pages/dashboard.py` | Plotly charts over application stats pulled from Supabase |
| `pages/my_profile.py` | Upload resume once, persist to Supabase `user_profiles` table |

### `src/` modules

- **`src/helper.py`** — All OpenAI calls. Uses `gpt-4.1` for resume tailoring and cover letter generation (high-quality, strict rules), `gpt-4o-mini` for lightweight tasks (summarise, extract post signal). Also owns `generate_resume_pdf()` (WeasyPrint) and `generate_linkedin_dm()`.
- **`src/job_api.py`** — Apify actor wrappers for LinkedIn (`BHzefUZlZRKWxkTck`), Naukri (`muhammetakkurtt/naukri-job-scraper`), Indeed (`hMvNSpz3JnHgl5jkh`), and LinkedIn Posts (`Wpp1BZ6yGWjySadk3`). All fetch functions are decorated with `@st.cache_data` and save immediately to DB. The LinkedIn post fetcher starts all 6 hashtag-search runs concurrently then waits for each.
- **`src/database.py`** — Dual-write storage: Supabase is primary, SQLite (`jobs_repository.db`) is the fallback. `init_db()` runs on every import, so SQLite is always bootstrapped. All read functions try Supabase first and fall back to SQLite on failure.
- **`src/ui_components.py`** — All card renderers (`render_linkedin_card`, `render_naukri_card`, `render_indeed_card`, `render_linkedin_post_card`) and the shared `_actions_block` helper that renders the "⚡ Actions" expander (Tailor Resume / Cover Letter / Full JD tabs). `JOB_CARD_CSS` is injected by every page that renders cards.
- **`src/location_utils.py`** — City normalisation: maps raw location strings from all three job sources to canonical city names. The alias table covers Indian cities and common spelling variants. `get_available_cities()` self-updates from loaded jobs.

### MCP server

`mcp_server.py` exposes `get_linkedin_jobs` and `get_naukri_jobs` as FastMCP tools, importing directly from `src/job_api`. Run independently from the Streamlit app — AI agents connect to it as an MCP server.

### Database schema (Supabase tables)

| Table | Key fields |
|---|---|
| `linkedin_jobs_v2` | `job_id` (PK), `title`, `company`, `location`, `salary`, `job_description`, `search_query`, `fetched_at`, `raw_data` (JSON) |
| `naukri_jobs_v2` | same schema as linkedin |
| `indeed_jobs` | `id` (PK), `position_name`, `company`, `raw_data` (JSONB — already a dict, not a string) |
| `linkedin_posts` | `urn` (PK), `author_name`, `text`, `url`, `posted_at`, `hashtag_source` |
| `job_applications` | `user_email`, `job_id`, `source`, `applied_at` |
| `user_profiles` | `user_email` (PK/upsert key), one profile per user |

**Important:** `indeed_jobs.raw_data` is stored as Supabase JSONB (returns a `dict` from the client), unlike LinkedIn/Naukri which store it as a JSON string. `_get_indeed_from_db()` handles both types.

### Resume tailoring & cover letter pipeline

Both features follow the same flow:
1. Load HTML template (`resume_template.html` or `cover_letter_template.html`) from the project root.
2. Call GPT-4.1 with a strict system prompt — the resume tailoring prompt explicitly forbids inventing experience, upgrading titles, or fabricating metrics.
3. Strip any markdown code fences the LLM may have wrapped around the HTML.
4. Call WeasyPrint to render HTML → PDF, save to disk, offer a `st.download_button`.

### Supabase Edge Functions (cron)

`supabase/functions/` contains two Deno edge functions — `fetch-linkedin-posts` and `save-linkedin-posts` — scheduled daily at 8 AM IST via `supabase/migrations/schedule_linkedin_posts_cron.sql`. The same fetch can be triggered manually from the Posts tab in Browse Jobs.

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
