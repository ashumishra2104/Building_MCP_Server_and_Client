import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const APIFY_TOKEN = Deno.env.get("APIFY_API_TOKEN")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SAVE_POSTS_URL = `${SUPABASE_URL}/functions/v1/save-linkedin-posts`;

// LinkedIn search URLs for PM hiring hashtags
const HASHTAG_SEARCHES = [
  "https://www.linkedin.com/search/results/content/?keywords=%23wearehiring%20%23productmanager&sortBy=date",
  "https://www.linkedin.com/search/results/content/?keywords=%23hiring%20%23productmanager%20%23bangalore&sortBy=date",
  "https://www.linkedin.com/search/results/content/?keywords=%23pmjobs%20%23india&sortBy=date",
  "https://www.linkedin.com/search/results/content/?keywords=%23hiring%20%23productmanager%20%23india&sortBy=date",
];

serve(async () => {
  const results: string[] = [];

  for (const searchUrl of HASHTAG_SEARCHES) {
    try {
      const res = await fetch(
        `https://api.apify.com/v2/acts/Wpp1BZ6yGWjySadk3/runs?token=${APIFY_TOKEN}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            searchUrl,
            maxResults: 30,
            proxy: { useApifyProxy: true, apifyProxyGroups: ["RESIDENTIAL"] },
            webhooks: [
              {
                eventTypes: ["ACTOR.RUN.SUCCEEDED"],
                requestUrl: SAVE_POSTS_URL,
                headersTemplate: `{"Authorization": "Bearer ${Deno.env.get("ANON_KEY")}"}`,
              },
            ],
          }),
        }
      );

      const { data } = await res.json();
      results.push(`Started run ${data?.id} for: ${searchUrl}`);
    } catch (err) {
      results.push(`Failed for ${searchUrl}: ${err}`);
    }
  }

  return new Response(JSON.stringify({ ok: true, results }), {
    headers: { "Content-Type": "application/json" },
  });
});
