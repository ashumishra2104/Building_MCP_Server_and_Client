import streamlit as st
import os
import re

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOB_CARD_CSS = """
<style>
.job-card {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 8px;
    border: 1px solid #e1e4e8;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    font-family: 'Inter', sans-serif;
    color: #1a1a1a;
}
.linkedin-card { border-left: 5px solid #0077b5; }
.naukri-card   { border-left: 5px solid #ff751a; }
.indeed-card   { border-left: 5px solid #2557a7; }
.post-card     { border-left: 5px solid #0a66c2; background: #f6f9fc; }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.job-title   { font-size: 17px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.company-info { display: flex; align-items: center; gap: 8px; color: #586069; font-size: 14px; }
.rating-badge { background: #fffcf0; border: 1px solid #ffd700; color: #b8860b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }

.meta-row  { display: flex; flex-wrap: wrap; gap: 12px; margin: 10px 0; color: #586069; font-size: 13px; }
.meta-item { display: flex; align-items: center; gap: 6px; }

.badge-container { display: flex; gap: 8px; }
.badge        { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-easy   { background-color: #e8f0fe; color: #1967d2; }
.badge-salary { background-color: #e6ffec; color: #055d20; }

.description-preview { font-size: 13px; color: #444; line-height: 1.5; margin: 10px 0;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.full-jd-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px;
    border-left: 4px solid #0077b5; font-size: 13px; color: #333; line-height: 1.6; }

.card-footer  { display: flex; justify-content: space-between; align-items: center;
    margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f3f5; }
.view-link  { color: #0077b5; text-decoration: none !important; font-weight: 600; font-size: 13px; }
.apply-btn  { background-color: #0077b5; color: #ffffff !important; padding: 8px 18px;
    border-radius: 8px; text-decoration: none !important; font-weight: 600; font-size: 13px; display: inline-block; }

.avatar { width: 40px; height: 40px; background: #f0f2f5; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: #65676b; font-size: 18px; flex-shrink: 0; }

.stExpander { border: none !important; box-shadow: none !important; margin-bottom: 20px !important; }
.stExpander > div { border: 1px solid #e1e4e8 !important; border-top: none !important;
    border-bottom-left-radius: 12px !important; border-bottom-right-radius: 12px !important; }

/* Pagination */
.page-btn-active {
    background: #0077b5; color: white; border-radius: 6px;
    padding: 6px 12px; font-weight: 700; text-align: center;
}
.page-btn {
    border: 1px solid #d0d7de; border-radius: 6px;
    padding: 6px 12px; text-align: center; cursor: pointer;
}
</style>
"""


def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]*?>', '', raw_html)
    clean = re.sub(r'\n+', '\n', clean).strip()
    return clean


def render_linkedin_card(job, idx, resume_text, candidate_name, key_prefix="l"):
    from src.helper import tailor_resume, generate_resume_pdf

    is_easy_apply = job.get('easyApply') or job.get('applyType') == 'EASY_APPLY'
    easy_apply_badge = '<span class="badge badge-easy">● Easy Apply</span>' if is_easy_apply else ""
    salary = job.get('salaryRange') or job.get('salary') or "Not Disclosed"
    company = job.get('companyName', job.get('company', 'Unknown Company')) or "Unknown"
    avatar_char = company[0].upper()
    job_url = job.get('url') or job.get('jobUrl') or job.get('link') or "#"
    posted_time = job.get('postedAt') or job.get('postDate') or job.get('relativeTime') or "Recently"
    full_desc = clean_html(job.get('jobDescription') or job.get('description') or "No description provided.")
    desc_preview = full_desc[:200] + "..." if len(full_desc) > 200 else full_desc

    st.markdown(f"""<div class="job-card linkedin-card">
<div style="display:flex;gap:14px;">
<div class="avatar">{avatar_char}</div>
<div style="flex-grow:1;">
<div class="card-header">
  <div><div class="job-title">{job.get('title','N/A')}</div><div class="company-info">{company}</div></div>
  <div class="badge-container">{easy_apply_badge}<span class="badge badge-salary">{salary}</span></div>
</div>
<div class="meta-row">
  <div class="meta-item">📍 {job.get('location','Global')}</div>
  <div class="meta-item">🕒 {posted_time}</div>
</div>
<div class="description-preview">{desc_preview}</div>
<div class="card-footer">
  <a href="{job_url}" target="_blank" class="view-link">🔗 View Job</a>
  <a href="{job_url}" target="_blank" class="apply-btn">Apply Now</a>
</div>
</div></div></div>""", unsafe_allow_html=True)

    with st.expander("Tailor Resume for this Job"):
        if resume_text:
            if st.button("✨ Create Customised Resume", key=f"tailor_{key_prefix}_{idx}"):
                with st.spinner("Tailoring your resume to this role..."):
                    template_path = os.path.join(APP_DIR, "resume_template.html")
                    try:
                        with open(template_path) as f:
                            html_template = f.read()
                        tailored_html = tailor_resume(resume_text, full_desc, html_template)
                        safe_company = "".join(c for c in company if c.isalnum())
                        pdf_filename = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                        if tailored_html:
                            if generate_resume_pdf(tailored_html, pdf_filename):
                                st.success(f"✅ Resume tailored for {company}!")
                                with open(pdf_filename, "rb") as f:
                                    st.download_button("📩 Download PDF", f, pdf_filename,
                                                       mime="application/pdf",
                                                       key=f"dl_{key_prefix}_{idx}")
                            else:
                                st.error("PDF generation failed. Check WeasyPrint dependencies.")
                        else:
                            st.error("Failed to tailor resume content.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("Upload your resume on the main page to enable tailoring.")

    with st.expander("Read More Details"):
        st.write(full_desc)


def render_naukri_card(job, idx, resume_text, candidate_name, key_prefix="n"):
    from src.helper import tailor_resume, generate_resume_pdf

    job_id = str(job.get('jobId', idx))
    job_url = job.get('jdURL') or job.get('url') or "#"
    ambition = job.get('ambitionBoxData')
    rating = ambition.get('AggregateRating') if isinstance(ambition, dict) else None
    rating_html = f'<span class="rating-badge">★ {rating}</span>' if rating else ""
    current_jd = job.get('jobDescription', '')
    is_snippet = len(current_jd) < 500

    st.markdown(f"""<div class="job-card naukri-card">
<div class="card-header">
  <div>
    <div class="job-title">{job.get('title','N/A')}</div>
    <div class="company-info">{job.get('companyName','')} {rating_html}</div>
  </div>
  <a href="{job_url}" target="_blank" class="view-link">🔗 View Job</a>
</div>
<div class="meta-row">
  <div class="meta-item">📍 {job.get('location','')}</div>
  <div class="meta-item">💰 {job.get('salary','Not Disclosed')}</div>
  <div class="meta-item">🕒 {job.get('footerPlaceholderLabel','Recently')}</div>
</div>
<div class="card-footer">
  <a href="{job_url}" target="_blank" class="apply-btn">Apply Now</a>
</div>
</div>""", unsafe_allow_html=True)

    with st.expander("Tailor Resume for this Job"):
        if resume_text:
            if st.button("✨ Create Customised Resume", key=f"tailor_{key_prefix}_{job_id}_{idx}"):
                jd_to_use = current_jd
                if is_snippet:
                    with st.spinner("Step 1/2: Fetching full description..."):
                        from src.job_api import fetch_full_details_batched
                        from src.database import save_jobs_to_db
                        results = fetch_full_details_batched([job_url])
                        if results and results[0].get('full_description'):
                            jd_to_use = results[0]['full_description']
                            job['jobDescription'] = jd_to_use
                            save_jobs_to_db("naukri", "manual", [job])
                        else:
                            st.error("Could not fetch full description. Proceeding with snippet.")
                with st.spinner("Step 2/2: Tailoring your resume..."):
                    template_path = os.path.join(APP_DIR, "resume_template.html")
                    try:
                        with open(template_path) as f:
                            html_template = f.read()
                        tailored_html = tailor_resume(resume_text, clean_html(jd_to_use), html_template)
                        company = job.get('companyName', 'Employer')
                        safe_company = "".join(c for c in company if c.isalnum())
                        pdf_filename = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                        if tailored_html:
                            if generate_resume_pdf(tailored_html, pdf_filename):
                                st.success("✅ Resume tailored!")
                                with open(pdf_filename, "rb") as f:
                                    st.download_button("📩 Download PDF", f, pdf_filename,
                                                       mime="application/pdf",
                                                       key=f"dl_{key_prefix}_{job_id}_{idx}")
                            else:
                                st.error("PDF generation failed.")
                        else:
                            st.error("Failed to tailor resume content.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("Upload your resume on the main page to enable tailoring.")

    with st.expander("Read More / Full Description"):
        if is_snippet:
            st.caption("⚠️ Current description is a snippet.")
            st.write(clean_html(current_jd))
            if st.button("🔍 Fetch Full Description", key=f"fetch_{key_prefix}_{job_id}_{idx}"):
                with st.spinner("Fetching..."):
                    from src.job_api import fetch_full_details_batched
                    from src.database import save_jobs_to_db
                    results = fetch_full_details_batched([job_url])
                    if results and results[0].get('full_description'):
                        job['jobDescription'] = results[0]['full_description']
                        save_jobs_to_db("naukri", "manual", [job])
                        st.rerun()
                    else:
                        st.error("Failed to fetch full description.")
        else:
            st.markdown(f"<div class='full-jd-box'>{clean_html(current_jd)}</div>", unsafe_allow_html=True)


def render_indeed_card(job, idx, resume_text, candidate_name, key_prefix="i"):
    from src.helper import tailor_resume, generate_resume_pdf
    import json as _json

    job_id    = str(job.get('id', idx))
    job_url   = job.get('externalApplyLink') or job.get('url') or "#"
    view_url  = job.get('url') or "#"
    company   = job.get('company') or "Unknown Company"
    avatar    = company[0].upper()
    title     = job.get('positionName') or "N/A"
    location  = job.get('location') or ""
    posted    = job.get('postedAt') or "Recently"
    salary    = job.get('salary') or "Not Disclosed"
    rating    = job.get('rating') or 0
    job_types = job.get('jobType') or []
    if isinstance(job_types, str):
        try:
            job_types = _json.loads(job_types)
        except Exception:
            job_types = [job_types]
    job_type_str = ", ".join(job_types) if job_types else "Full-time"

    rating_html = f'<span class="rating-badge">★ {rating}</span>' if rating else ""
    full_desc   = job.get('description') or ""
    desc_preview = full_desc[:200] + "..." if len(full_desc) > 200 else full_desc

    st.markdown(f"""<div class="job-card indeed-card">
<div style="display:flex;gap:14px;">
<div class="avatar">{avatar}</div>
<div style="flex-grow:1;">
<div class="card-header">
  <div>
    <div class="job-title">{title}</div>
    <div class="company-info">{company} {rating_html}</div>
  </div>
  <span class="badge badge-easy">{job_type_str}</span>
</div>
<div class="meta-row">
  <div class="meta-item">📍 {location}</div>
  <div class="meta-item">💰 {salary}</div>
  <div class="meta-item">🕒 {posted}</div>
</div>
<div class="description-preview">{desc_preview}</div>
<div class="card-footer">
  <a href="{view_url}" target="_blank" class="view-link">🔗 View on Indeed</a>
  <a href="{job_url}" target="_blank" class="apply-btn">Apply Now</a>
</div>
</div></div></div>""", unsafe_allow_html=True)

    with st.expander("Tailor Resume for this Job"):
        if resume_text:
            if st.button("✨ Create Customised Resume", key=f"tailor_{key_prefix}_{job_id}_{idx}"):
                with st.spinner("Tailoring your resume to this role..."):
                    template_path = os.path.join(APP_DIR, "resume_template.html")
                    try:
                        with open(template_path) as f:
                            html_template = f.read()
                        tailored_html = tailor_resume(resume_text, full_desc, html_template)
                        safe_company  = "".join(c for c in company if c.isalnum())
                        pdf_filename  = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                        if tailored_html:
                            if generate_resume_pdf(tailored_html, pdf_filename):
                                st.success(f"✅ Resume tailored for {company}!")
                                with open(pdf_filename, "rb") as f:
                                    st.download_button("📩 Download PDF", f, pdf_filename,
                                                       mime="application/pdf",
                                                       key=f"dl_{key_prefix}_{job_id}_{idx}")
                            else:
                                st.error("PDF generation failed. Check WeasyPrint dependencies.")
                        else:
                            st.error("Failed to tailor resume content.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("Upload your resume on the main page to enable tailoring.")

    with st.expander("Read Full Description"):
        st.markdown(f"<div class='full-jd-box'>{full_desc}</div>", unsafe_allow_html=True)


def render_linkedin_post_card(post):
    author      = post.get("author_name") or "Unknown"
    headline    = post.get("author_headline") or ""
    profile_url = post.get("author_profile_url") or "#"
    text        = post.get("text") or ""
    url         = post.get("url") or "#"
    posted      = post.get("time_since_posted") or ""
    avatar      = author[0].upper() if author else "?"
    preview     = text[:280] + "…" if len(text) > 280 else text

    st.markdown(f"""
<div class="job-card post-card">
  <div style="display:flex;gap:14px;align-items:flex-start;">
    <div class="avatar" style="background:#e8f0fe;color:#0a66c2;">{avatar}</div>
    <div style="flex-grow:1;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div class="job-title" style="color:#0a66c2;">
            <a href="{profile_url}" target="_blank" style="color:#0a66c2;text-decoration:none;">{author}</a>
          </div>
          <div style="font-size:13px;color:#586069;margin-bottom:8px;">{headline[:90]}{"…" if len(headline)>90 else ""}</div>
        </div>
        <div style="font-size:12px;color:#888;white-space:nowrap;margin-left:10px;">🕒 {posted}</div>
      </div>
      <div style="font-size:13px;color:#333;line-height:1.6;white-space:pre-wrap;">{preview}</div>
      <div class="card-footer" style="margin-top:12px;">
        <a href="{profile_url}" target="_blank" class="view-link">👤 View Profile</a>
        <a href="{url}" target="_blank" class="apply-btn" style="background:#0a66c2;">🔗 View Post</a>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    if len(text) > 280:
        with st.expander("Read full post", expanded=False):
            st.markdown(f"<div style='font-size:13px;line-height:1.7;white-space:pre-wrap;color:#333;'>{text}</div>",
                        unsafe_allow_html=True)
