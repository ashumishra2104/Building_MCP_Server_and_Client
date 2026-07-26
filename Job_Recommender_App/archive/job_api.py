import streamlit as st
import os
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables (this automatically populates os.environ)
load_dotenv(override=True)

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
apify_client = ApifyClient(APIFY_API_TOKEN)

from src.database import save_jobs_to_db

#Fetch linkedin jobs based on search query and location
@st.cache_data(show_spinner=False)
def fetch_linkedin_jobs(search_query, location="india", rows=60):
    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        }
    }
    run = apify_client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
    jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    
    # Save to persistent database
    save_jobs_to_db("linkedin", search_query, jobs)
    
    return jobs



# Fetch full descriptions from jdURLs in batch
def fetch_full_details_batched(urls):
    """Uses Playwright Scraper to handle JS-heavy job pages."""
    if not urls: return []
    
    run_input = {
        "startUrls": [{"url": url} for url in urls],
        "pageFunction": """async function pageFunction(context) {
            const { page } = context;
            // Wait for the description to load
            await page.waitForSelector('.jd-description, .job-desc, [class*="job-desc"]', { timeout: 10000 }).catch(() => {});
            
            const full_jd = await page.evaluate(() => {
                const el = document.querySelector('.jd-description') || 
                           document.querySelector('.job-desc') || 
                           document.querySelector('[class*="job-desc"]');
                return el ? el.innerText : "";
            });
            
            return {
                url: context.request.url,
                full_description: full_jd.trim()
            };
        }""",
        "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        "maxConcurrency": 5
    }
    
    # Playwright is required because Naukri is a JS-heavy React app
    run = apify_client.actor("apify/playwright-scraper").call(run_input=run_input)
    results = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    return results

# Fetch naukri jobs with option for deep scan
@st.cache_data(show_spinner=False)
def fetch_naukri_jobs(search_query, location="india", rows=60, deep_scan=False):
    run_input = {
        "keyword": search_query,
        "maxJobs": rows,
    }
    run = apify_client.actor("muhammetakkurtt/naukri-job-scraper").call(run_input=run_input)
    jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    
    # Save to persistent database (initial summary)
    save_jobs_to_db("naukri", search_query, jobs)
    
    # Optional: Immediately fetch full details for the top results
    if deep_scan and jobs:
        urls = [j.get('jdURL') for j in jobs[:10] if j.get('jdURL')] # Scan top 10 for speed
        full_details = fetch_full_details_batched(urls)
        
        # Map full JDs back to job objects
        jd_map = {res['url']: res['full_description'] for res in full_details if 'full_description' in res}
        for job in jobs:
            url = job.get('jdURL')
            if url in jd_map:
                job['jobDescription'] = jd_map[url]
        
        # Re-save with full descriptions
        save_jobs_to_db("naukri", search_query, jobs)
        
    return jobs



