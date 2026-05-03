-- Enable required extensions (run once in Supabase SQL editor)
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Schedule: every day at 8:00 AM IST = 02:30 UTC
-- Calls the fetch-linkedin-posts edge function which starts Apify runs
-- Apify webhooks handle saving results asynchronously via save-linkedin-posts

select cron.schedule(
  'fetch-linkedin-posts-daily',
  '30 2 * * *',
  $$
  select net.http_post(
    url     := current_setting('app.edge_function_url') || '/fetch-linkedin-posts',
    headers := jsonb_build_object(
                 'Content-Type',   'application/json',
                 'Authorization',  'Bearer ' || current_setting('app.anon_key')
               ),
    body    := '{}'::jsonb
  ) as request_id;
  $$
);

-- To verify the job is scheduled:
-- select * from cron.job;

-- To remove the job:
-- select cron.unschedule('fetch-linkedin-posts-daily');
