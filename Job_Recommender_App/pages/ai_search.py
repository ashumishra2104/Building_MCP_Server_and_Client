import streamlit as st
import os
from src.helper import extract_text_from_pdf, ask_openai
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs, fetch_indeed_jobs
from src.database import init_db
from src.ui_components import JOB_CARD_CSS, render_linkedin_card, render_naukri_card, render_indeed_card

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

init_db()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    if st.session_state.get("authenticated"):
        st.write("Logged in as: **demo@nomail.com**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["resume_analyzed"] = False
            st.rerun()
    st.divider()
    st.header("📊 Database Stats")
    try:
        from src.database import supabase as sb
        if sb:
            l_res = sb.table("linkedin_jobs_v2").select("*", count="exact").limit(1).execute()
            n_res = sb.table("naukri_jobs_v2").select("*", count="exact").limit(1).execute()
            i_res = sb.table("indeed_jobs").select("*", count="exact").limit(1).execute()
            st.write(f"📁 **LinkedIn Jobs cached:** {l_res.count}")
            st.write(f"📁 **Naukri Jobs cached:** {n_res.count}")
            st.write(f"📁 **Indeed Jobs cached:** {i_res.count}")
        else:
            st.write("Database not connected.")
    except Exception:
        st.write("Stats unavailable.")

# ── Login gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background:#fff;padding:30px;border-radius:16px;border:1px solid #e1e4e8;box-shadow:0 10px 25px rgba(0,0,0,0.1);'>
                <h2 style='text-align:center;color:#0077b5;margin-bottom:5px;'>🔓 Account Login</h2>
                <p style='text-align:center;color:#586069;font-size:14px;margin-bottom:25px;'>Enter your credentials to access the AI Job Recommender</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("📧 Email Address", placeholder="demo@nomail.com")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Launch Dashboard", use_container_width=True):
                if email == "demo@nomail.com" and password == "password":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid Email or Password")
    st.stop()

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
        with st.spinner("Analysing profile for best search results..."):
            designation = ask_openai(
                f"Identify the latest job title from this resume summary. Return only the title:\n\n{resume_summary}",
                max_tokens=50).strip()
            keywords = ask_openai(
                f"Suggest job titles and keywords for job search. Comma-separated list only:\n\n{resume_summary}",
                max_tokens=100).strip()
            linkedin_query = designation
            kw_cleaned = [k.strip() for k in keywords.split(",") if k.strip().lower() != designation.lower()]
            naukri_query = f"{designation} " + " ".join(kw_cleaned[:3])
            st.session_state['linkedin_query'] = linkedin_query
            st.session_state['naukri_query'] = naukri_query

        with st.spinner(f"Fetching jobs for: {linkedin_query} & {naukri_query}"):
            st.session_state['linkedin_jobs'] = fetch_linkedin_jobs(linkedin_query, rows=60)
            st.session_state['naukri_jobs']   = fetch_naukri_jobs(naukri_query, rows=60)
            st.session_state['indeed_jobs']   = fetch_indeed_jobs(linkedin_query, location="India", country="IN", rows=50)

    if 'linkedin_jobs' in st.session_state:
        st.markdown("---")
        st.header("🏢 LinkedIn Jobs")
        st.info(f"🔍 Search: **{st.session_state.get('linkedin_query', '')}**")
        if not st.session_state['linkedin_jobs']:
            st.warning("No LinkedIn jobs found. Try refining your resume.")
        for i, job in enumerate(st.session_state['linkedin_jobs']):
            render_linkedin_card(job, i, resume_text, candidate_name, key_prefix="l")

    if 'naukri_jobs' in st.session_state:
        st.markdown("---")
        st.header("💼 Naukri Jobs (India)")
        st.info(f"🔍 Search: **{st.session_state.get('naukri_query', '')}**")
        if not st.session_state['naukri_jobs']:
            st.warning("No Naukri jobs found. Try adjusting your profile summary.")
        for i, job in enumerate(st.session_state['naukri_jobs']):
            render_naukri_card(job, i, resume_text, candidate_name, key_prefix="n")

    if 'indeed_jobs' in st.session_state:
        st.markdown("---")
        st.header("🔵 Indeed Jobs (India)")
        st.info(f"🔍 Search: **{st.session_state.get('linkedin_query', '')}**")
        if not st.session_state['indeed_jobs']:
            st.warning("No Indeed jobs found. Try refining your resume.")
        for i, job in enumerate(st.session_state['indeed_jobs']):
            render_indeed_card(job, i, resume_text, candidate_name, key_prefix="i")
