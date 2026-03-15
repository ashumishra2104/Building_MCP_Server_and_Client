import streamlit.elements.layouts
import streamlit as st
import os
from src.helper import extract_text_from_pdf, ask_openai, tailor_resume, generate_resume_pdf
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs
from src.database import init_db

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize database
init_db()

# --- Authentication System ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login_page():
    st.set_page_config(page_title="AI Job Recommender - Login", page_icon="💼")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background-color: #ffffff; padding: 30px; border-radius: 16px; border: 1px solid #e1e4e8; box-shadow: 0 10px 25px rgba(0,0,0,0.1);'>
                <h2 style='text-align: center; color: #0077b5; margin-bottom: 5px;'>🔓 Account Login</h2>
                <p style='text-align: center; color: #586069; font-size: 14px; margin-bottom: 25px;'>Enter your credentials to access the AI Job Recommender</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("📧 Email Address", placeholder="demo@nomail.com")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Launch Dashboard", use_container_width=True)
            
            if submit:
                if email == "demo@nomail.com" and password == "password":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid Email or Password")

if not st.session_state["authenticated"]:
    login_page()
    st.stop()


# Sidebar for controls and stats
with st.sidebar:
    st.header("👤 Account")
    st.write(f"Logged in as: **demo@nomail.com**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()
    
    st.header("📊 Database Stats")
    try:
        from src.database import supabase as sb
        if sb:
            l_res = sb.table("linkedin_jobs_v2").select("*", count="exact").limit(1).execute()
            n_res = sb.table("naukri_jobs_v2").select("*", count="exact").limit(1).execute()
            st.write(f"📁 **LinkedIn Jobs cached:** {l_res.count}")
            st.write(f"📁 **Naukri Jobs cached:** {n_res.count}")
        else:
            st.write("Database not connected.")
    except Exception as e:
        st.write("Stats unavailable.")

st.title("💼  AI Job Recommender System")
st.markdown("""Upload your resume and get reccomendations based on your job skills and experience from Linkedin and Naukri.
""")    

# Custom CSS for Premium Job Cards
st.markdown("""
    <style>
    .job-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 8px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
    }
    .linkedin-card { border-left: 5px solid #0077b5; }
    .naukri-card { border-left: 5px solid #ff751a; }
    
    .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .job-title { font-size: 20px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
    .company-info { display: flex; align-items: center; gap: 8px; color: #586069; font-size: 16px; }
    .rating-badge { background: #fffcf0; border: 1px solid #ffd700; color: #b8860b; padding: 2px 8px; border-radius: 4px; font-size: 13px; font-weight: 600; }
    
    .meta-row { display: flex; flex-wrap: wrap; gap: 16px; margin: 12px 0; color: #586069; font-size: 14px; }
    .meta-item { display: flex; align-items: center; gap: 6px; }
    
    .badge-container { display: flex; gap: 8px; margin-top: 8px; }
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-easy { background-color: #e8f0fe; color: #1967d2; }
    .badge-salary { background-color: #e6ffec; color: #055d20; }
    
    .description-preview { font-size: 14px; color: #444; line-height: 1.5; margin: 12px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .full-jd-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #0077b5; font-size: 14px; color: #333; line-height: 1.6; }
    
    .card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding-top: 12px; border-top: 1px solid #f1f3f5; }
    .view-link { color: #0077b5; text-decoration: none !important; font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 4px; }
    .apply-btn { background-color: #0077b5; color: #ffffff !important; padding: 10px 24px; border-radius: 8px; text-decoration: none !important; font-weight: 600; font-size: 14px; display: inline-block; }
    
    .avatar { width: 48px; height: 48px; background: #f0f2f5; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #65676b; font-size: 20px; }
    
    /* Style Streamlit expander to blend in */
    .stExpander { border: none !important; box-shadow: none !important; margin-bottom: 24px !important; }
    .stExpander > div { border: 1px solid #e1e4e8 !important; border-top: none !important; border-bottom-left-radius: 12px !important; border-bottom-right-radius: 12px !important; }
    </style>
""", unsafe_allow_html=True)

def clean_html(raw_html):
    import re
    if not raw_html: return ""
    clean = re.sub(r'<[^>]*?>', '', raw_html)
    clean = re.sub(r'\n+', '\n', clean).strip()
    return clean

uploaded_file = st.file_uploader("Upload your resume", type=["pdf"])

if uploaded_file:
    if 'resume_text' not in st.session_state:
        with st.spinner("Extracting text from resume..."):
            st.session_state['resume_text'] = extract_text_from_pdf(uploaded_file)
            st.success("Text extracted successfully")
   
    resume_text = st.session_state['resume_text']

    # Summarize with session state
    if 'resume_summary' not in st.session_state:
        with st.spinner("Summarizing your resume..."):
            st.session_state['resume_summary'] = ask_openai(f"Summarise this resume highlighting the skills,education, and experience: \n\n {resume_text}",max_tokens=1000)
            st.session_state['candidate_name'] = ask_openai(f"Extract the full name of the candidate from this resume text. Return only the name: \n\n {resume_text[:1000]}", max_tokens=50)

    resume_summary = st.session_state['resume_summary']
    candidate_name = st.session_state.get('candidate_name', 'Candidate').strip().split('\n')[0]

    st.markdown("---")
    st.header("📄 Resume Summary")
    st.markdown(f"<div style='background-color: #f8f9fa; color: #1a1a1a; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8;'>{resume_summary}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🛠️ Skill Gaps & Missing Areas")
    if 'skill_gaps' not in st.session_state:
        with st.spinner("Finding skill gaps..."):
            st.session_state['skill_gaps'] = ask_openai(f"Based on this resume suggest skill gaps and certifications needed to improve this person's carrer: \n\n {resume_summary}",max_tokens=1000)
    st.markdown(f"<div style='background-color: #f8f9fa; color: #1a1a1a; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8;'>{st.session_state['skill_gaps']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🚀 Future Roadmap & Preparation Strategy")
    if 'future_roadmap' not in st.session_state:
        with st.spinner("Creating Future roadmap..."):
            st.session_state['future_roadmap'] = ask_openai(f"Based on this resume suggest a future roadmap to imporve this person's carrer: \n\n {resume_summary}",max_tokens=1000)
    st.markdown(f"<div style='background-color: #f8f9fa; color: #1a1a1a; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8;'>{st.session_state['future_roadmap']}</div>", unsafe_allow_html=True)

    st.success("✅ Analysis Completed Successfully!")

    if st.button(" 🧲 Get Job Recommendations 🧲"):
        with st.spinner("Analyzing profile for best search results..."):
            designation = ask_openai(f"Identify the latest or current job title/designation from this resume summary. Return only the title name: \n\n {resume_summary}", max_tokens=50).strip()
            keywords = ask_openai(f"Based on this resume summary suggest the best job titles and keywords for searching jobs. Give a comma separated list of keywords only, no explaination \n\n {resume_summary}", max_tokens=100).strip()
            
            # Optimized queries
            linkedin_query = designation
            # Combine Designation + top 3 Keywords for highly filtered Naukri results
            kw_cleaned = [k.strip() for k in keywords.split(",") if k.strip().lower() != designation.lower()]
            naukri_query = f"{designation} " + " ".join(kw_cleaned[:3])
            
            st.session_state['linkedin_query'] = linkedin_query
            st.session_state['naukri_query'] = naukri_query

        with st.spinner(f"Fetching jobs for: {linkedin_query} & {naukri_query}"):
            st.session_state['linkedin_jobs'] = fetch_linkedin_jobs(linkedin_query, rows=60)
            st.session_state['naukri_jobs'] = fetch_naukri_jobs(naukri_query, rows=60)

    # LinkedIn Results
    if 'linkedin_jobs' in st.session_state:
        st.markdown("---")
        l_query = st.session_state.get('linkedin_query', 'Profile Match')
        st.header(f"🏢 LinkedIn Jobs")
        st.info(f"🔍 **Search Basis (Designation):** {l_query}")
        
        if not st.session_state['linkedin_jobs']:
            st.warning("No LinkedIn jobs found for this designation. Try refining your resume summary.")
        for i, job in enumerate(st.session_state['linkedin_jobs']):
            # LinkedIn Easy Apply check (Based on Apify actor data keys)
            is_easy_apply = job.get('easyApply') or job.get('applyType') == 'EASY_APPLY'
            easy_apply_badge = '<span class="badge badge-easy">● Easy Apply</span>' if is_easy_apply else ""
            
            salary = job.get('salaryRange') or job.get('salary') or "Not Disclosed"
            company = job.get('companyName', job.get('company', 'Unknown Company'))
            avatar_char = company[0].upper() if company else "L"
            job_url = job.get('url') or job.get('jobUrl') or job.get('link') or "#"
            posted_time = job.get('postedAt') or job.get('postDate') or job.get('relativeTime') or "Recently"
            full_desc = clean_html(job.get('jobDescription') or job.get('description') or "No description provided.")
            desc_preview = full_desc[:200] + "..." if len(full_desc) > 200 else full_desc

            st.markdown(f"""<div class="job-card linkedin-card">
<div style="display: flex; gap: 16px;">
<div class="avatar">{avatar_char}</div>
<div style="flex-grow: 1;">
<div class="card-header">
<div><div class="job-title">{job.get('title')}</div><div class="company-info">{company}</div></div>
<div class="badge-container">{easy_apply_badge}<span class="badge badge-salary">{salary}</span></div>
</div>
<div class="meta-row">
<div class="meta-item">📍 {job.get('location', 'Global')}</div>
<div class="meta-item">🕒 Posted {posted_time}</div>
</div>
<div class="description-preview">{desc_preview}</div>
<div class="card-footer">
<a href="{job_url}" target="_blank" class="view-link">🔗 View Job</a>
<a href="{job_url}" target="_blank" class="apply-btn">Apply Now</a>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
            
            with st.expander("Tailor Resume for this Job"):
                if st.button(f"✨ Create Customised Resume", key=f"tailor_l_{i}"):
                    with st.spinner("Magic in progress... Tailoring your resume to this role."):
                        # Load template
                        template_path = os.path.join(APP_DIR, "resume_template.html")
                        try:
                            with open(template_path, "r") as f:
                                html_template = f.read()
                            
                            tailored_html = tailor_resume(resume_text, full_desc, html_template)
                            
                            safe_company = "".join([c for c in company if c.isalnum()])
                            pdf_filename = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                            
                            if tailored_html:
                                success = generate_resume_pdf(tailored_html, pdf_filename)
                                if success:
                                    st.success(f"✅ Resume successfully tailored for {company}!")
                                    with open(pdf_filename, "rb") as f:
                                        st.download_button(
                                            label="📩 Download Tailored Resume (PDF)",
                                            data=f,
                                            file_name=pdf_filename,
                                            mime="application/pdf"
                                        )
                                else:
                                    st.error("Failed to generate PDF. check if weasyprint and its dependencies are installed.")
                            else:
                                st.error("Failed to tailor resume content.")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with st.expander("Read More Details"):
                st.write(full_desc)

    if 'naukri_jobs' in st.session_state:
        st.markdown("---")
        n_query = st.session_state.get('naukri_query', 'Skills Match')
        st.header(f"💼 Naukri Jobs (India)")
        st.info(f"🔍 **Search Basis (Keywords):** {n_query}")
        
        if not st.session_state['naukri_jobs']:
            st.warning("No Naukri jobs found for these keywords. Try adjusting your profile summary.")
        from src.job_api import fetch_full_details_batched

        for i, job in enumerate(st.session_state['naukri_jobs']):
            job_id = str(job.get('jobId', i))
            job_url = job.get('jdURL') or job.get('url') or "#"
            rating = job.get('ambitionBoxData', {}).get('AggregateRating')
            rating_html = f'<span class="rating-badge">★ {rating}</span>' if rating else ""
            
            # Check if we already have the full JD in memory or DB
            current_jd = job.get('jobDescription', '')
            is_snippet = len(current_jd) < 500 # Heuristic for a snippet
            
            st.markdown(f"""<div class="job-card naukri-card">
<div class="card-header">
<div><div class="job-title">{job.get('title')}</div><div class="company-info">{job.get('companyName')} {rating_html}</div></div>
<a href="{job_url}" target="_blank" class="view-link">🔗 View Job</a>
</div>
<div class="meta-row">
<div class="meta-item">📍 {job.get('location')}</div>
<div class="meta-item">💰 {job.get('salary', 'Not Disclosed')}</div>
<div class="meta-item">🕒 Posted {job.get('footerPlaceholderLabel', 'Recently')}</div>
</div>
</div>""", unsafe_allow_html=True)
            
            with st.expander("Tailor Resume for this Job"):
                if st.button(f"✨ Create Customised Resume", key=f"tailor_n_{job_id}"):
                    # 1. Sequential Fetch if needed
                    jd_to_use = current_jd
                    if is_snippet:
                        with st.spinner("Step 1/2: Fetching 100% Full description from Naukri..."):
                            full_results = fetch_full_details_batched([job_url])
                            if full_results and full_results[0].get('full_description'):
                                jd_to_use = full_results[0]['full_description']
                                job['jobDescription'] = jd_to_use
                                # Update database
                                from src.database import save_jobs_to_db
                                save_jobs_to_db("naukri", st.session_state.get('naukri_query','manual'), [job])
                            else:
                                st.error("Could not fetch full description. Proceeding with snippet (not recommended).")
                    
                    # 2. Tailoring
                    with st.spinner("Step 2/2: Tailoring your resume with GPT-4o..."):
                        template_path = os.path.join(APP_DIR, "resume_template.html")
                        try:
                            with open(template_path, "r") as f:
                                html_template = f.read()
                            
                            tailored_html = tailor_resume(resume_text, clean_html(jd_to_use), html_template)
                            
                            company = job.get('companyName', 'Naukri_Employer')
                            safe_company = "".join([c for c in company if c.isalnum()])
                            pdf_filename = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                            
                            if tailored_html:
                                success = generate_resume_pdf(tailored_html, pdf_filename)
                                if success:
                                    st.success(f"✅ Resume successfully tailored!")
                                    with open(pdf_filename, "rb") as f:
                                        st.download_button(
                                            label="📩 Download Tailored Resume (PDF)",
                                            data=f,
                                            file_name=pdf_filename,
                                            mime="application/pdf",
                                            key=f"dl_n_{job_id}"
                                        )
                                else:
                                    st.error("Failed to generate PDF. Check WeasyPrint dependencies.")
                            else:
                                st.error("Failed to tailor resume content.")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with st.expander("Read More / Fetch Full Details"):
                if is_snippet:
                    st.write("⚠️ *Current description is a snippet.*")
                    st.write(clean_html(current_jd))
                    if st.button(f"🔍 Fetch 100% Full Description", key=f"fetch_{job_id}"):
                        with st.spinner("Deep scanning job page..."):
                            full_results = fetch_full_details_batched([job_url])
                            if full_results and full_results[0].get('full_description'):
                                new_jd = full_results[0]['full_description']
                                job['jobDescription'] = new_jd
                                # Update database too
                                from src.database import save_jobs_to_db
                                save_jobs_to_db("naukri", st.session_state.get('naukri_query','manual'), [job])
                                st.rerun()
                            else:
                                st.error("Failed to fetch full description. The page might be protected or changed.")
                else:
                    st.write("✅ **Full Description Fetched**")
                    st.markdown(f"<div class='full-jd-box'>{clean_html(current_jd)}</div>", unsafe_allow_html=True)