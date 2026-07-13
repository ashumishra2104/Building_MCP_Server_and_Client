import streamlit as st
import os
from dotenv import load_dotenv
from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

load_dotenv(override=True)

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

from src.database import save_jobs_to_db, save_linkedin_posts_to_db, get_user_settings

USER_EMAIL = "demo@nomail.com"  # single-user demo app


def _get_apify_client():
    """Builds an ApifyClient using the user's saved key (My Profile → Scraper Settings),
    falling back to the app's default APIFY_API_TOKEN from .env."""
    try:
        user_key = get_user_settings(USER_EMAIL).get("apify_api_key", "")
    except Exception:
        user_key = ""
    return ApifyClient(user_key.strip() if user_key else APIFY_API_TOKEN)


@st.cache_data(show_spinner=False)
def fetch_linkedin_jobs(search_query, location="india", rows=60):
    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }
    try:
        client = _get_apify_client()
        run = client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        jobs = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        save_jobs_to_db("linkedin", search_query, jobs)
        return jobs
    except ApifyApiError as e:
        _show_apify_error("LinkedIn", str(e))
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching LinkedIn jobs: {e}")
        return []


@st.cache_data(show_spinner=False)
def fetch_naukri_jobs(search_query, rows=60, deep_scan=False):
    run_input = {"keyword": search_query, "maxJobs": rows}
    try:
        client = _get_apify_client()
        run = client.actor("muhammetakkurtt/naukri-job-scraper").call(run_input=run_input)
        jobs = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        save_jobs_to_db("naukri", search_query, jobs)

        if deep_scan and jobs:
            urls = [j.get('jdURL') for j in jobs[:10] if j.get('jdURL')]
            full_details = fetch_full_details_batched(urls)
            jd_map = {r['url']: r['full_description'] for r in full_details if 'full_description' in r}
            for job in jobs:
                if job.get('jdURL') in jd_map:
                    job['jobDescription'] = jd_map[job['jdURL']]
            save_jobs_to_db("naukri", search_query, jobs)

        return jobs
    except ApifyApiError as e:
        _show_apify_error("Naukri", str(e))
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching Naukri jobs: {e}")
        return []


def fetch_full_details_batched(urls):
    if not urls:
        return []
    run_input = {
        "startUrls": [{"url": u} for u in urls],
        "pageFunction": """async function pageFunction(context) {
            const { page } = context;
            await page.waitForSelector('.jd-description, .job-desc, [class*="job-desc"]', { timeout: 10000 }).catch(() => {});
            const full_jd = await page.evaluate(() => {
                const el = document.querySelector('.jd-description') ||
                           document.querySelector('.job-desc') ||
                           document.querySelector('[class*="job-desc"]');
                return el ? el.innerText : "";
            });
            return { url: context.request.url, full_description: full_jd.trim() };
        }""",
        "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        "maxConcurrency": 5,
    }
    try:
        client = _get_apify_client()
        run = client.actor("apify/playwright-scraper").call(run_input=run_input)
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())
    except ApifyApiError as e:
        _show_apify_error("Playwright scraper", str(e))
        return []
    except Exception as e:
        st.error(f"Error fetching full job details: {e}")
        return []


@st.cache_data(show_spinner=False)
def fetch_indeed_jobs(search_query, location="India", country="IN", rows=50):
    run_input = {
        "country": country,
        "followApplyRedirects": False,
        "location": location,
        "maxItemsPerSearch": rows,
        "parseCompanyDetails": False,
        "position": search_query,
        "saveOnlyUniqueItems": True,
    }
    try:
        client = _get_apify_client()
        run = client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)
        jobs = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        save_jobs_to_db("indeed", search_query, jobs)
        return jobs
    except ApifyApiError as e:
        _show_apify_error("Indeed", str(e))
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching Indeed jobs: {e}")
        return []


LINKEDIN_POST_SEARCHES = [
    "https://www.linkedin.com/search/results/content/?keywords=%23wearehiring%20%23productmanager&sortBy=date",
    "https://www.linkedin.com/search/results/content/?keywords=%23pmjobs%20%23india&sortBy=date",
    "https://www.linkedin.com/search/results/content/?keywords=%23hiring%20%23productmanager%20%23india&sortBy=date",
    "https://www.linkedin.com/search/results/content/?keywords=%23ProductManagement%20%23ProductLeadership%20%23Hiring&sortBy=date",
    "https://www.linkedin.com/search/results/content/?keywords=%23ProductManagement%20%23ProductLeadership%20%23Hiring%20%23HiringIndia%20%23SeniorProductManager&sortBy=date",
    "https://www.linkedin.com/search/results/content/?keywords=%23AIProductManagement%20%23GenAI%20%23ProductManagement%20%23HiringIndia%20%23Hiring&sortBy=date",
]


def fetch_linkedin_posts(max_results=30):
    """Fetch LinkedIn hiring posts across 4 hashtag searches, save to Supabase."""
    all_posts = []
    try:
        client = _get_apify_client()
        # Start all 4 runs concurrently
        runs = []
        for url in LINKEDIN_POST_SEARCHES:
            run = client.actor("Wpp1BZ6yGWjySadk3").start(
                run_input={"urls": [url], "maxResults": max_results}
            )
            runs.append(run)

        # Wait for each and collect items
        for run in runs:
            try:
                client.run(run["id"]).wait_for_finish()
                items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                all_posts.extend(items)
            except Exception as e:
                st.warning(f"A post scrape run failed: {e}")

        saved = save_linkedin_posts_to_db(all_posts)
        return saved, len(all_posts)
    except ApifyApiError as e:
        _show_apify_error("LinkedIn Posts", str(e))
        return 0, 0
    except Exception as e:
        st.error(f"Unexpected error fetching LinkedIn posts: {e}")
        return 0, 0


def fetch_poster_email(profile_url: str) -> str:
    """Return email for a LinkedIn profile URL, or empty string on failure."""
    try:
        client = _get_apify_client()
        run = client.actor("anchor/linkedin-to-email").call(
            run_input={"startUrls": [{"url": profile_url}]}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        return (items[0].get("email") or "") if items else ""
    except Exception as e:
        print(f"fetch_poster_email error: {e}")
        return ""


def _show_apify_error(source: str, raw_msg: str):
    is_paid = "rent" in raw_msg.lower() or "trial" in raw_msg.lower() or "redacted" in raw_msg.lower()
    if is_paid:
        st.warning(
            f"⚠️ **{source} scraper requires a paid Apify subscription.** "
            f"The free trial for this actor has expired.  \n"
            f"👉 You can still browse all **{source} jobs already saved** in the database — "
            f"use **📁 Browse Saved Jobs** in the sidebar.",
            icon="💳",
        )
    else:
        st.error(f"Apify error ({source}): {raw_msg}")
