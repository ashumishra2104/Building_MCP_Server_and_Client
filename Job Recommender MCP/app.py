import streamlit.elements.layouts
import streamlit as st
from src.helper import extract_text_from_pdf, ask_openai
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs


st.set_page_config(page_title="Job Recommender", layout="wide")

st.title("💼  AI Job Recommender System")
st.markdown("""Upload your resume and get reccomendations based on your job skills and experience from Linkedin and Naukri.
""")    

uploaded_file = st.file_uploader("Upload your resume", type=["pdf"])

if uploaded_file:
    with st.spinner("Extracting text from resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)
        st.success("Text extracted successfully")
   
    # Summarize the resume
    st.markdown("---")
    st.header("📄 Resume Summary")
    with st.spinner("Summarizing your resume..."):
        resume_summary = ask_openai(f"Summarise this resume highlighting the skills,education, and experience: \n\n {resume_text}",max_tokens=1000)
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px;'>{resume_summary}</div>", unsafe_allow_html=True)
    st.success("Resume summarized successfully")

    # Find skill gaps
    st.markdown("---")
    st.header("🛠️ Skill Gaps & Missing Areas")
    with st.spinner("Finding skill gaps..."):
        skill_gaps = ask_openai(f"Based on this resume suggest skill gaps and certifications needed to improve this person's carrer: \n\n {resume_summary}",max_tokens=1000)
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px;'>{skill_gaps}</div>", unsafe_allow_html=True)
    st.success("Skill gaps found successfully") 

    # Create Future roadmap
    st.markdown("---")
    st.header("🚀 Future Roadmap & Preparation Strategy")
    with st.spinner("Creating Future roadmap..."):
        future_roadmap = ask_openai(f"Based on this resume suggest a future roadmap to imporve this person's carrer: \n\n {resume_summary}",max_tokens=1000)
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px;'>{future_roadmap}</div>", unsafe_allow_html=True)
    st.success("Future roadmap created successfully") 

    st.success("✅ Analysis Completed Successfully!")


    if st.button(" 🧲 Get Job Recommendations 🧲"):
        with st.spinner("Fetching jobs based on resume summary..."):
            keywords = ask_openai(f"Based on this resume summary suggest the best job titles and keywords for searching jobs. Give a comma separated list of keywords only, no explaination \n\n {resume_summary}", max_tokens=100)
            search_keywords_cleaned = [k.strip() for k in keywords.replace("\n", "").split(",")]
            search_query_str = " ".join(search_keywords_cleaned)

        st.success(f"Extracted Job keywords: {search_keywords_cleaned}")

        with st.spinner("Fetching jobs from Linkedin and Naukri..."):
            linkedin_jobs = fetch_linkedin_jobs(search_query_str, rows=60)
            naukri_jobs = fetch_naukri_jobs(search_query_str, rows=60)

        st.markdown("---")
        st.header("🏢 Top LinkedIn Jobs")

        if linkedin_jobs:
            for job in linkedin_jobs:
                st.markdown(f"**{job.get('title')}** at *{job.get('companyName')}*")
                st.markdown(f"- 📍 {job.get('location')}")
                st.markdown(f"- 🔗 [View Job]({job.get('url')})")
                st.markdown("---")
        else:
            st.warning("No LinkedIn jobs found.")

        st.markdown("---")
        st.header("💼 Top Naukri Jobs (India)")

        if naukri_jobs:
            for job in naukri_jobs:
                st.markdown(f"**{job.get('title')}** at *{job.get('companyName')}*")
                st.markdown(f"- 📍 {job.get('location')}")
                st.markdown(f"- 🔗 [View Job]({job.get('jdURL')})")
                st.markdown("---")
        else:
            st.warning("No Naukri jobs found.")
            
        st.success("✅ Job Recommendations Fetched Successfully!")