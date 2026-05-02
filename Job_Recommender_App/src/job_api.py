import streamlit as st
import os
from dotenv import load_dotenv
from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

load_dotenv(override=True)

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
apify_client = ApifyClient(APIFY_API_TOKEN)

from src.database import save_jobs_to_db


@st.cache_data(show_spinner=False)
def fetch_linkedin_jobs(search_query, location="india", rows=60):
    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }
    try:
        run = apify_client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
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
        run = apify_client.actor("muhammetakkurtt/naukri-job-scraper").call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
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
        run = apify_client.actor("apify/playwright-scraper").call(run_input=run_input)
        return list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
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
        run = apify_client.actor("hMvNSpz3JnHgl5jkh").call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        save_jobs_to_db("indeed", search_query, jobs)
        return jobs
    except ApifyApiError as e:
        _show_apify_error("Indeed", str(e))
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching Indeed jobs: {e}")
        return []


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
