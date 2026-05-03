# LinkedIn Posts — Daily Cron via Supabase Edge Functions

## How it works

```
pg_cron (8 AM IST)
    └─▶ fetch-linkedin-posts  (starts 4 Apify runs, one per hashtag combo)
              └─▶ Apify webhook ──▶ save-linkedin-posts  (fetches dataset, dedupes, upserts)
```

- `fetch-linkedin-posts` returns in < 3 s — no timeout risk.
- `save-linkedin-posts` is called by Apify automatically when each run succeeds.
- Dedup: upsert on `urn` (PRIMARY KEY) — safe to re-run.
- Filter: posts older than 15 days are skipped at save time.

## Deploy

### 1. Install Supabase CLI
```bash
brew install supabase/tap/supabase
supabase login
supabase link --project-ref <your-project-ref>
```

### 2. Set secrets
```bash
supabase secrets set APIFY_API_TOKEN=<your-apify-token>
# SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected automatically
# SUPABASE_ANON_KEY needs to be set manually:
supabase secrets set SUPABASE_ANON_KEY=<your-anon-key>
```

### 3. Deploy both functions
```bash
supabase functions deploy fetch-linkedin-posts
supabase functions deploy save-linkedin-posts
```

### 4. Set up pg_cron (Supabase SQL Editor)

First, store config as Postgres settings (one-time):
```sql
alter database postgres set app.edge_function_url = 'https://<project-ref>.supabase.co/functions/v1';
alter database postgres set app.anon_key = '<your-anon-key>';
```

Then run the migration SQL:
```bash
# paste contents of supabase/migrations/schedule_linkedin_posts_cron.sql into Supabase SQL editor
```

### 5. Verify
```sql
select * from cron.job;
```
You should see `fetch-linkedin-posts-daily` scheduled at `30 2 * * *`.

### 6. Test manually (optional)
```bash
supabase functions serve fetch-linkedin-posts --env-file .env
curl -X POST http://localhost:54321/functions/v1/fetch-linkedin-posts
```
