import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const APIFY_TOKEN = Deno.env.get("APIFY_API_TOKEN")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

const FIFTEEN_DAYS_MS = 15 * 24 * 60 * 60 * 1000;

serve(async (req) => {
  // Apify webhook payload: { eventData: { actorRunId, defaultDatasetId }, ... }
  const body = await req.json();
  const datasetId = body?.eventData?.defaultDatasetId;

  if (!datasetId) {
    return new Response("No datasetId in payload", { status: 400 });
  }

  // Fetch all items from the dataset
  const itemsRes = await fetch(
    `https://api.apify.com/v2/datasets/${datasetId}/items?token=${APIFY_TOKEN}&format=json&clean=true`
  );
  const items: Record<string, unknown>[] = await itemsRes.json();

  const now = Date.now();
  const records = [];

  for (const item of items) {
    const urn = item.urn as string | undefined;
    if (!urn) continue;

    // 15-day filter
    const isoDate = item.postedAtISO as string | undefined;
    if (isoDate) {
      const postAge = now - new Date(isoDate).getTime();
      if (postAge > FIFTEEN_DAYS_MS) continue;
    }

    // Skip reposts (no original content)
    if (item.repostedPost) continue;

    records.push({
      urn,
      author_name: item.authorName ?? null,
      author_headline: item.authorHeadline ?? null,
      author_profile_url: item.authorProfileUrl ?? null,
      text: item.text ?? null,
      url: item.url ?? null,
      posted_at: isoDate ?? null,
      time_since_posted: item.timeSincePosted ?? null,
      is_repost: false,
      author_type: item.authorType ?? null,
      hashtag_source: (item.searchUrl as string | undefined) ?? null,
      scraped_at: new Date().toISOString(),
    });
  }

  if (records.length === 0) {
    return new Response(JSON.stringify({ ok: true, saved: 0 }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  // Upsert — URN is PRIMARY KEY, so duplicates are silently ignored
  const { error } = await supabase
    .from("linkedin_posts")
    .upsert(records, { onConflict: "urn", ignoreDuplicates: true });

  if (error) {
    console.error("Supabase upsert error:", error);
    return new Response(JSON.stringify({ ok: false, error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  console.log(`Saved ${records.length} posts from dataset ${datasetId}`);
  return new Response(JSON.stringify({ ok: true, saved: records.length }), {
    headers: { "Content-Type": "application/json" },
  });
});
