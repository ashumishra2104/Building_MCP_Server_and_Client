import streamlit as st
import os
import re
from urllib.parse import urlparse, parse_qs, unquote_plus

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_EMAIL = "demo@nomail.com"

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

.badge-container { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.badge        { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-easy   { background-color: #e8f0fe; color: #1967d2; }
.badge-salary { background-color: #e6ffec; color: #055d20; }

.applied-chip {
    display: inline-block; font-size: 10px; font-weight: 700;
    padding: 3px 10px; border-radius: 12px; white-space: nowrap;
    margin-bottom: 4px;
}
.chip-applied   { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.chip-unapplied { background: #f0f4fb; color: #888;    border: 1px solid #d0d7de; }

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
</style>
"""


def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]*?>', '', raw_html)
    clean = re.sub(r'\n+', '\n', clean).strip()
    return clean


# ── Shared action helpers ──────────────────────────────────────────────────────

def _tailor_tab(resume_text, full_desc, company, candidate_name, key_prefix):
    from src.helper import tailor_resume, generate_resume_pdf
    from src.database import get_ats_keywords
    if not resume_text:
        st.info("Save your resume in My Profile to enable tailoring.")
        return

    # Auto-load approved ATS keywords (cached in session)
    if "ats_approved_keywords" not in st.session_state:
        st.session_state["ats_approved_keywords"] = get_ats_keywords(USER_EMAIL, status="approved")
    approved_keywords = [k["keyword"] for k in st.session_state["ats_approved_keywords"]]
    if approved_keywords:
        st.caption(f"ℹ️ {len(approved_keywords)} ATS keywords will be auto-injected from your approved list.")

    if st.button("✨ Create Customised Resume", key=f"tailor_{key_prefix}"):
        with st.spinner("Tailoring your resume to this role..."):
            template_path = os.path.join(APP_DIR, "resume_template.html")
            try:
                with open(template_path) as f:
                    html_template = f.read()
                tailored_html = tailor_resume(resume_text, full_desc, html_template,
                                              approved_keywords=approved_keywords or None)
                safe_company  = "".join(c for c in company if c.isalnum())
                pdf_filename  = f"{candidate_name.replace(' ', '_')}_Tailored_{safe_company}.pdf"
                if tailored_html:
                    if generate_resume_pdf(tailored_html, pdf_filename):
                        st.success(f"✅ Resume tailored for {company}!")
                        with open(pdf_filename, "rb") as f:
                            st.download_button("📩 Download PDF", f, pdf_filename,
                                               mime="application/pdf",
                                               key=f"dl_resume_{key_prefix}")
                    else:
                        st.error("PDF generation failed.")
                else:
                    st.error("Failed to tailor resume content.")
            except Exception as e:
                st.error(f"Error: {e}")


def _cover_letter_tab(resume_text, full_desc, company, job_title, candidate_name, key_prefix):
    from src.helper import generate_cover_letter, _extract_cover_letter_text, generate_resume_pdf
    if not resume_text:
        st.info("Save your resume in My Profile to enable cover letter generation.")
        return

    state_key = f"cl_html_{key_prefix}"
    if st.button("✍️ Generate Cover Letter", key=f"gen_cl_{key_prefix}"):
        cl_template_path = os.path.join(APP_DIR, "cover_letter_template.html")
        try:
            with open(cl_template_path) as f:
                cl_template = f.read()
        except FileNotFoundError:
            st.error("Cover letter template not found.")
            return
        with st.spinner("Writing your cover letter…"):
            filled_html = generate_cover_letter(resume_text, full_desc, cl_template,
                                                company=company, job_title=job_title)
        if filled_html:
            st.session_state[state_key] = filled_html
        else:
            st.error("Failed to generate cover letter. Please try again.")

    filled_html = st.session_state.get(state_key)
    if filled_html:
        preview_text = _extract_cover_letter_text(filled_html)
        st.markdown("---")
        for para in preview_text.split("\n\n"):
            para = para.strip()
            if para:
                st.markdown(para)
        st.markdown("---")
        safe_company = "".join(c for c in company if c.isalnum())
        pdf_filename = f"{candidate_name.replace(' ', '_')}_CoverLetter_{safe_company}.pdf"
        if generate_resume_pdf(filled_html, pdf_filename):
            with open(pdf_filename, "rb") as f:
                st.download_button("📩 Download Cover Letter PDF", f, pdf_filename,
                                   mime="application/pdf", key=f"dl_cl_{key_prefix}")


def _actions_block(job_id, source, full_desc, company, job_title,
                   resume_text, candidate_name, key_prefix):
    """Applied chip toggle + single ⚡ Actions expander with 3 tabs."""
    from src.database import toggle_job_application

    applied_ids = st.session_state.get("applied_job_ids", set())
    is_applied  = str(job_id) in applied_ids

    # Small chip-style applied toggle
    col_chip, _ = st.columns([1.4, 4])
    with col_chip:
        label     = "✅ Applied" if is_applied else "○ Mark Applied"
        btn_type  = "primary" if is_applied else "secondary"
        if st.button(label, key=f"tog_{key_prefix}", type=btn_type, use_container_width=True):
            now_applied = toggle_job_application(USER_EMAIL, job_id, source)
            if now_applied:
                applied_ids.add(str(job_id))
            else:
                applied_ids.discard(str(job_id))
            st.session_state["applied_job_ids"] = applied_ids
            st.rerun()

    # Single Actions expander
    with st.expander("⚡ Actions"):
        tab1, tab2, tab3 = st.tabs(["📄 Tailor Resume", "✍️ Cover Letter", "📖 Full JD"])
        with tab1:
            _tailor_tab(resume_text, full_desc, company, candidate_name, key_prefix)
        with tab2:
            _cover_letter_tab(resume_text, full_desc, company, job_title, candidate_name, key_prefix)
        with tab3:
            st.markdown(f"<div class='full-jd-box'>{full_desc}</div>", unsafe_allow_html=True)


# ── Card renderers ─────────────────────────────────────────────────────────────

def render_linkedin_card(job, idx, resume_text, candidate_name, key_prefix="l"):
    is_easy_apply = job.get('easyApply') or job.get('applyType') == 'EASY_APPLY'
    easy_apply_badge = '<span class="badge badge-easy">● Easy Apply</span>' if is_easy_apply else ""
    salary      = job.get('salaryRange') or job.get('salary') or "Not Disclosed"
    company     = job.get('companyName', job.get('company', 'Unknown Company')) or "Unknown"
    avatar_char = company[0].upper()
    job_url     = job.get('url') or job.get('jobUrl') or job.get('link') or "#"
    posted_time = job.get('postedAt') or job.get('postDate') or job.get('relativeTime') or "Recently"
    full_desc   = clean_html(job.get('jobDescription') or job.get('description') or "No description provided.")
    desc_preview = full_desc[:200] + "..." if len(full_desc) > 200 else full_desc
    job_id      = str(job.get('jobId') or job.get('id') or job.get('url') or idx)

    applied_ids = st.session_state.get("applied_job_ids", set())
    is_applied  = str(job_id) in applied_ids
    chip_class  = "chip-applied" if is_applied else "chip-unapplied"
    chip_label  = "✓ Applied" if is_applied else "○ Not Applied"

    st.markdown(f"""<div class="job-card linkedin-card">
<div style="display:flex;gap:14px;">
<div class="avatar">{avatar_char}</div>
<div style="flex-grow:1;">
<div class="card-header">
  <div><div class="job-title">{job.get('title','N/A')}</div><div class="company-info">{company}</div></div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
    <span class="applied-chip {chip_class}">{chip_label}</span>
    <div class="badge-container">{easy_apply_badge}<span class="badge badge-salary">{salary}</span></div>
  </div>
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

    _actions_block(job_id, "linkedin", full_desc, company, job.get('title', ''),
                   resume_text, candidate_name, key_prefix=f"{key_prefix}_l_{idx}")


def render_naukri_card(job, idx, resume_text, candidate_name, key_prefix="n"):
    job_id      = str(job.get('jobId', idx))
    job_url     = job.get('jdURL') or job.get('url') or "#"
    company     = job.get('companyName', '') or "Unknown"
    ambition    = job.get('ambitionBoxData')
    rating      = ambition.get('AggregateRating') if isinstance(ambition, dict) else None
    rating_html = f'<span class="rating-badge">★ {rating}</span>' if rating else ""
    current_jd  = job.get('jobDescription', '')
    is_snippet  = len(current_jd) < 500
    full_desc   = clean_html(current_jd)

    applied_ids = st.session_state.get("applied_job_ids", set())
    is_applied  = str(job_id) in applied_ids
    chip_class  = "chip-applied" if is_applied else "chip-unapplied"
    chip_label  = "✓ Applied" if is_applied else "○ Not Applied"

    st.markdown(f"""<div class="job-card naukri-card">
<div class="card-header">
  <div>
    <div class="job-title">{job.get('title','N/A')}</div>
    <div class="company-info">{company} {rating_html}</div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
    <span class="applied-chip {chip_class}">{chip_label}</span>
    <a href="{job_url}" target="_blank" class="view-link">🔗 View Job</a>
  </div>
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

    # For Full JD tab: handle snippet vs full
    if is_snippet:
        jd_content = (f"<p style='color:#888;font-size:12px;'>⚠️ Snippet only — use Fetch Full JD below.</p>"
                      f"<div class='full-jd-box'>{full_desc}</div>")
    else:
        jd_content = f"<div class='full-jd-box'>{full_desc}</div>"

    applied_ids2 = st.session_state.get("applied_job_ids", set())
    is_applied2  = str(job_id) in applied_ids2
    col_chip, _ = st.columns([1.4, 4])
    with col_chip:
        label    = "✅ Applied" if is_applied2 else "○ Mark Applied"
        btn_type = "primary" if is_applied2 else "secondary"
        if st.button(label, key=f"tog_{key_prefix}_n_{job_id}_{idx}", type=btn_type, use_container_width=True):
            from src.database import toggle_job_application
            now_applied = toggle_job_application(USER_EMAIL, job_id, "naukri")
            if now_applied: applied_ids2.add(str(job_id))
            else: applied_ids2.discard(str(job_id))
            st.session_state["applied_job_ids"] = applied_ids2
            st.rerun()

    with st.expander("⚡ Actions"):
        tab1, tab2, tab3 = st.tabs(["📄 Tailor Resume", "✍️ Cover Letter", "📖 Full JD"])
        with tab1:
            _tailor_tab(resume_text, full_desc, company, candidate_name,
                        key_prefix=f"{key_prefix}_n_{job_id}_{idx}")
        with tab2:
            _cover_letter_tab(resume_text, full_desc, company, job.get('title', ''),
                              candidate_name, key_prefix=f"{key_prefix}_n_{job_id}_{idx}")
        with tab3:
            st.markdown(jd_content, unsafe_allow_html=True)
            if is_snippet:
                if st.button("🔍 Fetch Full Description",
                             key=f"fetch_{key_prefix}_n_{job_id}_{idx}"):
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


def render_indeed_card(job, idx, resume_text, candidate_name, key_prefix="i"):
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
        try: job_types = _json.loads(job_types)
        except Exception: job_types = [job_types]
    job_type_str = ", ".join(job_types) if job_types else "Full-time"
    rating_html  = f'<span class="rating-badge">★ {rating}</span>' if rating else ""
    full_desc    = job.get('description') or ""
    desc_preview = full_desc[:200] + "..." if len(full_desc) > 200 else full_desc

    applied_ids = st.session_state.get("applied_job_ids", set())
    is_applied  = str(job_id) in applied_ids
    chip_class  = "chip-applied" if is_applied else "chip-unapplied"
    chip_label  = "✓ Applied" if is_applied else "○ Not Applied"

    st.markdown(f"""<div class="job-card indeed-card">
<div style="display:flex;gap:14px;">
<div class="avatar">{avatar}</div>
<div style="flex-grow:1;">
<div class="card-header">
  <div>
    <div class="job-title">{title}</div>
    <div class="company-info">{company} {rating_html}</div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
    <span class="applied-chip {chip_class}">{chip_label}</span>
    <span class="badge badge-easy">{job_type_str}</span>
  </div>
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

    _actions_block(job_id, "indeed", full_desc, company, title,
                   resume_text, candidate_name, key_prefix=f"{key_prefix}_i_{job_id}_{idx}")


def _post_actions_block(post_text, author_name, resume_text, candidate_name, key_prefix):
    """⚡ Actions expander for LinkedIn posts: Tailor Resume + LinkedIn DM."""
    if not resume_text:
        with st.expander("⚡ Actions"):
            st.info("Save your resume in My Profile to enable actions.")
        return

    with st.expander("⚡ Actions"):
        tab1, tab2 = st.tabs(["📄 Tailor Resume", "💬 LinkedIn DM"])

        with tab1:
            st.caption("Relevant keywords will be extracted from this post before tailoring.")
            if st.button("✨ Tailor Resume to Post", key=f"tailor_post_{key_prefix}"):
                from src.helper import extract_post_job_signal, tailor_resume, generate_resume_pdf
                with st.spinner("Extracting job signals from post…"):
                    job_signal = extract_post_job_signal(post_text)
                with st.spinner("Tailoring your resume…"):
                    template_path = os.path.join(APP_DIR, "resume_template.html")
                    try:
                        with open(template_path) as f:
                            html_template = f.read()
                        tailored_html = tailor_resume(resume_text, job_signal, html_template)
                        if tailored_html:
                            safe = "".join(c for c in (author_name or "Post") if c.isalnum())
                            pdf_filename = f"{candidate_name.replace(' ', '_')}_Tailored_{safe}.pdf"
                            if generate_resume_pdf(tailored_html, pdf_filename):
                                st.success("✅ Resume tailored!")
                                with open(pdf_filename, "rb") as f:
                                    st.download_button("📩 Download PDF", f, pdf_filename,
                                                       mime="application/pdf",
                                                       key=f"dl_post_{key_prefix}")
                            else:
                                st.error("PDF generation failed.")
                        else:
                            st.error("Failed to tailor resume.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with tab2:
            dm_key = f"dm_text_{key_prefix}"
            st.caption("Short LinkedIn DM — copy and send directly on LinkedIn.")
            if st.button("💬 Generate DM", key=f"gen_dm_{key_prefix}"):
                from src.helper import generate_linkedin_dm
                with st.spinner("Writing your LinkedIn message…"):
                    dm = generate_linkedin_dm(resume_text, post_text, author_name)
                if dm:
                    st.session_state[dm_key] = dm
                else:
                    st.error("Failed to generate DM. Please try again.")

            saved_dm = st.session_state.get(dm_key)
            if saved_dm:
                st.markdown("---")
                st.text_area("Copy & paste this into LinkedIn:",
                             value=saved_dm, height=160,
                             key=f"dm_area_{key_prefix}",
                             label_visibility="collapsed")


# ── Utility ────────────────────────────────────────────────────────────────────

def normalize_hashtag_source(source: str) -> str:
    if not source:
        return ""
    if source.startswith("http"):
        qs  = parse_qs(urlparse(source).query)
        raw = qs.get("keywords", [""])[0]
        return unquote_plus(raw).replace("%23", "#")
    return " ".join(f"#{w}" for w in source.replace("-", " ").split("+"))


def render_linkedin_post_card(post, resume_text="", candidate_name="Candidate"):
    author      = post.get("author_name") or "Unknown"
    headline    = post.get("author_headline") or ""
    profile_url = post.get("author_profile_url") or "#"
    text        = post.get("text") or ""
    url         = post.get("url") or "#"
    posted      = post.get("time_since_posted") or ""
    keyword     = normalize_hashtag_source(post.get("hashtag_source") or "")
    avatar      = author[0].upper() if author else "?"
    preview     = text[:280] + "…" if len(text) > 280 else text
    kw_badge    = (f'<span style="background:#e8f0fe;color:#0a66c2;font-size:11px;font-weight:600;'
                   f'padding:2px 8px;border-radius:12px;white-space:nowrap;">{keyword}</span>'
                   if keyword else "")

    post_id    = url
    applied_ids = st.session_state.get("applied_job_ids", set())
    is_applied  = str(post_id) in applied_ids
    chip_class  = "chip-applied" if is_applied else "chip-unapplied"
    chip_label  = "✓ Applied" if is_applied else "○ Not Applied"

    st.markdown(f"""
<div class="job-card post-card">
  <div style="display:flex;gap:14px;align-items:flex-start;">
    <div class="avatar" style="background:#e8f0fe;color:#0a66c2;">{avatar}</div>
    <div style="flex-grow:1;">
      <div class="card-header">
        <div>
          <div class="job-title" style="color:#0a66c2;">
            <a href="{profile_url}" target="_blank" style="color:#0a66c2;text-decoration:none;">{author}</a>
          </div>
          <div class="company-info" style="margin-bottom:6px;">{headline[:90]}{"…" if len(headline)>90 else ""}</div>
          {kw_badge}
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
          <span class="applied-chip {chip_class}">{chip_label}</span>
          <div style="font-size:12px;color:#888;white-space:nowrap;">🕒 {posted}</div>
        </div>
      </div>
      <div style="font-size:13px;color:#333;line-height:1.6;white-space:pre-wrap;margin-top:10px;">{preview}</div>
      <div class="card-footer">
        <a href="{profile_url}" target="_blank" class="view-link">👤 View Profile</a>
        <a href="{url}" target="_blank" class="apply-btn" style="background:#0a66c2;">🔗 View Post</a>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    key_prefix = f"p_{abs(hash(url)) % 100000}"

    col_chip, _ = st.columns([1.4, 4])
    with col_chip:
        label    = "✅ Applied" if is_applied else "○ Mark Applied"
        btn_type = "primary" if is_applied else "secondary"
        if st.button(label, key=f"tog_post_{key_prefix}", type=btn_type, use_container_width=True):
            from src.database import toggle_job_application
            now_applied = toggle_job_application(USER_EMAIL, post_id, "linkedin_post")
            if now_applied:
                applied_ids.add(str(post_id))
            else:
                applied_ids.discard(str(post_id))
            st.session_state["applied_job_ids"] = applied_ids
            st.rerun()

    if len(text) > 280:
        with st.expander("Read full post", expanded=False):
            st.markdown(f"<div style='font-size:13px;line-height:1.7;white-space:pre-wrap;color:#333;'>{text}</div>",
                        unsafe_allow_html=True)

    _post_actions_block(text, author, resume_text, candidate_name, key_prefix)
