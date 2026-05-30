import streamlit as st
import os
from src.helper import extract_text_from_pdf, ask_openai, generate_search_titles
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs, fetch_indeed_jobs
from src.database import init_db, get_user_settings, get_applied_job_ids
from src.ui_components import JOB_CARD_CSS, render_linkedin_card, render_naukri_card, render_indeed_card

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

init_db()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write("Logged in as: **demo@nomail.com**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_analyzed", "resume_text", "candidate_name",
                    "active_profile", "resume_summary", "skill_gaps"):
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()
    st.header("📊 Database Stats")
    try:
        from src.database import supabase as sb
        if sb:
            l_res = sb.table("linkedin_jobs_v2").select("*", count="exact").limit(1).execute()
            n_res = sb.table("naukri_jobs_v2").select("*", count="exact").limit(1).execute()
            i_res = sb.table("indeed_jobs").select("*", count="exact").limit(1).execute()
            p_res = sb.table("linkedin_posts").select("*", count="exact").limit(1).execute()
            st.write(f"📁 **LinkedIn Jobs:** {l_res.count}")
            st.write(f"📁 **Naukri Jobs:** {n_res.count}")
            st.write(f"📁 **Indeed Jobs:** {i_res.count}")
            st.write(f"📢 **LinkedIn Posts:** {p_res.count}")
    except Exception:
        st.write("Stats unavailable.")

# ── Main content ───────────────────────────────────────────────────────────────
st.markdown(JOB_CARD_CSS, unsafe_allow_html=True)
st.title("💼 AI Job Recommender System")
st.markdown("Upload your resume to get AI-powered job recommendations from LinkedIn, Naukri and Indeed.")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    if 'resume_text' not in st.session_state:
        with st.spinner("Extracting text from resume..."):
            st.session_state['resume_text'] = extract_text_from_pdf(uploaded_file)
        st.success("Text extracted successfully")

    resume_text = st.session_state['resume_text']

    if 'resume_summary' not in st.session_state:
        with st.spinner("Summarising your resume..."):
            st.session_state['resume_summary'] = ask_openai(
                f"Summarise this resume highlighting skills, education and experience:\n\n{resume_text}",
                max_tokens=1000)
            st.session_state['candidate_name'] = ask_openai(
                f"Extract the full name from this resume. Return only the name:\n\n{resume_text[:1000]}",
                max_tokens=50)

    resume_summary = st.session_state['resume_summary']
    candidate_name = st.session_state.get('candidate_name', 'Candidate').strip().split('\n')[0]

    st.markdown("---")
    st.header("📄 Resume Summary")
    st.markdown(f"<div style='background:#f8f9fa;color:#1a1a1a;padding:20px;border-radius:12px;border:1px solid #e1e4e8;'>{resume_summary}</div>",
                unsafe_allow_html=True)

    st.markdown("---")
    st.header("🛠️ Skill Gaps & Missing Areas")
    if 'skill_gaps' not in st.session_state:
        with st.spinner("Finding skill gaps..."):
            st.session_state['skill_gaps'] = ask_openai(
                f"Suggest skill gaps and certifications to improve this person's career:\n\n{resume_summary}",
                max_tokens=1000)
    st.markdown(f"<div style='background:#f8f9fa;color:#1a1a1a;padding:20px;border-radius:12px;border:1px solid #e1e4e8;'>{st.session_state['skill_gaps']}</div>",
                unsafe_allow_html=True)

    st.markdown("---")
    st.header("🚀 Future Roadmap & Preparation Strategy")
    if 'future_roadmap' not in st.session_state:
        with st.spinner("Creating future roadmap..."):
            st.session_state['future_roadmap'] = ask_openai(
                f"Suggest a future roadmap to improve this person's career:\n\n{resume_summary}",
                max_tokens=1000)
    st.markdown(f"<div style='background:#f8f9fa;color:#1a1a1a;padding:20px;border-radius:12px;border:1px solid #e1e4e8;'>{st.session_state['future_roadmap']}</div>",
                unsafe_allow_html=True)

    st.success("✅ Analysis Completed! Head to **📁 Browse Saved Jobs** in the left sidebar to explore all cached jobs.")
    st.session_state["resume_analyzed"] = True

    st.markdown("---")
    st.subheader("🔍 Fetch Fresh Job Recommendations (via Apify)")
    st.caption("This fetches live jobs from LinkedIn, Naukri and Indeed using the Apify API.")

    if st.button("🧲 Get Job Recommendations"):
        settings      = st.session_state.get("scraper_settings") or get_user_settings("demo@nomail.com")
        linkedin_rows = settings.get("linkedin_rows", 100)
        naukri_rows   = settings.get("naukri_rows",   150)
        indeed_rows   = settings.get("indeed_rows",    75)

        with st.spinner("Analysing profile for best search titles…"):
            config        = generate_search_titles(resume_summary)
            search_titles = config.get("search_titles", ["Product Manager"])
            current_title = config.get("current_title", search_titles[0])
            st.session_state["search_titles"]  = search_titles
            st.session_state["current_title"]  = current_title

        # ── LinkedIn: 3 separate searches, dedup by jobId/id/url ────────────
        linkedin_titles = search_titles[:3]
        with st.spinner(f"LinkedIn — searching: {' · '.join(linkedin_titles)}"):
            all_linkedin, seen_linkedin = [], set()
            for title in linkedin_titles:
                for job in (fetch_linkedin_jobs(title, rows=linkedin_rows) or []):
                    jid = str(job.get("jobId") or job.get("id") or job.get("url") or "")
                    if not jid or jid not in seen_linkedin:
                        if jid:
                            seen_linkedin.add(jid)
                        all_linkedin.append(job)
            st.session_state["linkedin_jobs"]  = all_linkedin
            st.session_state["linkedin_query"] = " · ".join(linkedin_titles)

        # ── Naukri: all titles joined as one keyword string ───────────────────
        naukri_query = " ".join(search_titles[:5])
        with st.spinner(f"Naukri — searching: {naukri_query}"):
            st.session_state["naukri_jobs"]  = fetch_naukri_jobs(naukri_query, rows=naukri_rows)
            st.session_state["naukri_query"] = naukri_query

        # ── Indeed: 3 separate searches, dedup by id/url ─────────────────────
        indeed_titles = search_titles[:3]
        with st.spinner(f"Indeed — searching: {' · '.join(indeed_titles)}"):
            all_indeed, seen_indeed = [], set()
            for title in indeed_titles:
                for job in (fetch_indeed_jobs(title, location="India", country="IN", rows=indeed_rows) or []):
                    jid = str(job.get("id") or job.get("url") or "")
                    if not jid or jid not in seen_indeed:
                        if jid:
                            seen_indeed.add(jid)
                        all_indeed.append(job)
            st.session_state["indeed_jobs"]  = all_indeed
            st.session_state["indeed_query"] = " · ".join(indeed_titles)

    # ── Fetch summary ─────────────────────────────────────────────────────────
    has_any = any(k in st.session_state for k in ("linkedin_jobs", "naukri_jobs", "indeed_jobs"))
    if has_any:
        if "applied_job_ids" not in st.session_state:
            st.session_state["applied_job_ids"] = get_applied_job_ids("demo@nomail.com")
        applied_ids = st.session_state["applied_job_ids"]

        li_jobs = st.session_state.get("linkedin_jobs", [])
        na_jobs = st.session_state.get("naukri_jobs",   [])
        in_jobs = st.session_state.get("indeed_jobs",   [])

        li_applied = sum(1 for i, j in enumerate(li_jobs)
                         if str(j.get("jobId") or j.get("id") or j.get("url") or i) in applied_ids)
        na_applied = sum(1 for i, j in enumerate(na_jobs)
                         if str(j.get("jobId", i)) in applied_ids)
        in_applied = sum(1 for i, j in enumerate(in_jobs)
                         if str(j.get("id", i)) in applied_ids)

        total      = len(li_jobs) + len(na_jobs) + len(in_jobs)
        total_applied = li_applied + na_applied + in_applied

        st.markdown("---")
        st.subheader("📊 Fetch Summary")
        c0, c1, c2, c3 = st.columns(4)
        c0.metric("Total Fetched", total, help="Across all three sources")
        c1.metric("LinkedIn", len(li_jobs), f"{li_applied} applied" if li_applied else "0 applied")
        c2.metric("Naukri",   len(na_jobs), f"{na_applied} applied" if na_applied else "0 applied")
        c3.metric("Indeed",   len(in_jobs), f"{in_applied} applied" if in_applied else "0 applied")
        if total_applied:
            st.info(f"✅ You've already applied to **{total_applied}** of these {total} jobs — they'll show the Applied badge on their cards.")

    if "linkedin_jobs" in st.session_state:
        st.markdown("---")
        st.header("🏢 LinkedIn Jobs")
        st.info(f"🔍 Searched: **{st.session_state.get('linkedin_query', '')}**  —  {len(st.session_state['linkedin_jobs'])} unique jobs")
        if not st.session_state["linkedin_jobs"]:
            st.warning("No LinkedIn jobs found. Try refining your resume.")
        for i, job in enumerate(st.session_state["linkedin_jobs"]):
            render_linkedin_card(job, i, resume_text, candidate_name, key_prefix="l")

    if "naukri_jobs" in st.session_state:
        st.markdown("---")
        st.header("💼 Naukri Jobs (India)")
        st.info(f"🔍 Searched: **{st.session_state.get('naukri_query', '')}**  —  {len(st.session_state['naukri_jobs'])} jobs")
        if not st.session_state["naukri_jobs"]:
            st.warning("No Naukri jobs found. Try adjusting your profile summary.")
        for i, job in enumerate(st.session_state["naukri_jobs"]):
            render_naukri_card(job, i, resume_text, candidate_name, key_prefix="n")

    if "indeed_jobs" in st.session_state:
        st.markdown("---")
        st.header("🔵 Indeed Jobs (India)")
        st.info(f"🔍 Searched: **{st.session_state.get('indeed_query', '')}**  —  {len(st.session_state['indeed_jobs'])} unique jobs")
        if not st.session_state["indeed_jobs"]:
            st.warning("No Indeed jobs found. Try refining your resume.")
        for i, job in enumerate(st.session_state["indeed_jobs"]):
            render_indeed_card(job, i, resume_text, candidate_name, key_prefix="i")
