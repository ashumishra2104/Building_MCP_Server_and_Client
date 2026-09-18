# New Machine Setup — Independent Backend Instance

This doc is for standing up **this same codebase on a different machine, with its
own independent Supabase project and Apify account** (not sharing the original
deployment's data/credentials). It assumes whoever's reading this — human or a
fresh Claude Code session with no memory of prior conversations — has just
cloned the repo and is starting cold.

**Read `CLAUDE.md` first** for the full app architecture, page layout, and
database schema reference. This doc only covers what's *different* about
bringing this repo up fresh with brand-new backend services, plus real
gotchas hit while doing this the first time.

---

## 1. Clone the repo

```bash
git clone https://github.com/ashumishra2104/Building_MCP_Server_and_Client.git
cd Building_MCP_Server_and_Client/Job_Recommender_App
```

## 2. macOS gotcha: Xcode license blocks *everything*

If `git`, `brew`, or basically any dev tool fails with:
```
You have not agreed to the Xcode license agreements...
```
Run this once, in an interactive Terminal (needs your password, then type
`agree` at the prompt):
```bash
sudo xcodebuild -license
```
This blocks `git status`, `brew install`, and any Homebrew formula/cask
install until accepted — it's not specific to any one tool. Hit this while
setting up the original machine; do it early on a fresh one too.

## 3. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**WeasyPrint on macOS** (used for resume/cover-letter PDF generation) needs
Homebrew's `pango`:
```bash
brew install pango
```
`src/helper.py` sets `DYLD_LIBRARY_PATH` automatically at import time to find it.

## 4. Set up a brand-new, independent Supabase project

1. Create a new project at [supabase.com](https://supabase.com).
2. Open its **SQL Editor** → paste the entire contents of
   [`supabase/full_schema_for_new_project.sql`](supabase/full_schema_for_new_project.sql)
   → **Run**. This creates all 9 tables the app touches, verified directly
   against every `supabase.table(...)` call in `src/database.py` (not just
   the smaller SQLite fallback subset).
3. Grab the new project's **URL** and **`service_role` (secret) key**
   (Project Settings → API). Use the secret key, not the public `anon` key —
   this app was built assuming service-role-level access and doesn't set up
   per-user RLS policies (see the schema file's own header comment for why
   RLS is deliberately left disabled).

**Do not use this repo's Supabase CLI link for this.** `supabase/.temp/linked-project.json`
is already linked to the *original* deployment's project — running
`supabase db push` or any Supabase CLI command from this repo would target
the wrong project. The SQL file is meant to be pasted manually into the new
project's dashboard.

## 5. Set up a brand-new Apify account

Sign up separately, generate a new API token (Settings → Integrations →
Personal API tokens). No schema/provisioning needed — Apify actors are
called on demand.

**Known limitation:** the LinkedIn job scraper actor (`BHzefUZlZRKWxkTck`)
requires a `RESIDENTIAL` proxy group, which needs a paid Apify plan — on a
free-trial Apify account this actor's calls may fail with a "requires paid
subscription" style error (`_show_apify_error` in `src/job_api.py` detects
and surfaces this specifically). Naukri/Indeed actors don't have this
requirement.

## 6. OpenAI key

Open question at time of writing — decide whether to reuse the original
deployment's `OPENAI_API_KEY` or provision a separate one for this instance.
Not yet decided as of this doc's creation.

## 7. Create `.env`

`.env` is gitignored and does **not** travel with `git clone` — create it
fresh:

```
OPENAI_API_KEY=
APIFY_API_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
```

Fill in the new Supabase URL/key from step 4, new Apify token from step 5,
and the OpenAI key per step 6.

## 8. Run it

```bash
streamlit run app.py
```

Login is hardcoded for this demo app: `demo@nomail.com` / `password`
(see `pages/login.py`).

---

## Notes from setting up the original instance (useful context, not required reading)

- **`get_user_settings()` "Could not find table 'public.user_settings'" warnings**
  were observed repeatedly in the original project's logs — despite
  `user_settings` being a documented table. This suggests it may never have
  actually been created there; the code silently falls back to SQLite
  defaults (`{100, 150, 75}` rows) when this happens, so it's not fatal, just
  worth knowing if you ever port data from the original project rather than
  starting fresh. The new schema file in this repo creates `user_settings`
  explicitly, so this instance won't have that gap.
- **Per-user Apify key caching**: `_get_apify_client()` in `src/job_api.py`
  checks `user_settings.apify_api_key` first and only falls back to the
  `.env` token if that's empty. If you ever see fetches running under an
  unexpected Apify account, check that column in `user_settings` before
  assuming `.env` is wrong.
- **`job_api.py` error visibility**: fetch functions print real exceptions to
  console in addition to calling `st.error()`/`st.warning()`, since those
  Streamlit calls silently no-op when code runs outside a live Streamlit
  session (e.g. a standalone script) — a real failure there previously
  looked identical to "0 jobs, no error," which cost real debugging time.
- **Poster email lookup** (`fetch_poster_email()` in `src/job_api.py`) uses
  `pequod-labs/linkedin-profile-verified-email`, a pay-per-verified-result
  Apify actor, and only returns an email when `emailConfidence == "verified"`
  — unverified catch-all guesses are discarded rather than returned. This
  replaced an earlier actor (`anchor/linkedin-to-email`) that had no such
  verification and was producing wrong addresses.
