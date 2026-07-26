import streamlit as st
import os
import json
from src.helper import (
    tailor_resume,
    generate_cover_letter,
    generate_resume_pdf,
    generate_linkedin_dm,
    extract_text_from_pdf,
    ask_openai,
    _extract_cover_letter_text,
)
from src.database import get_active_profile, get_ats_keywords, get_star_stories, save_star_stories
from src.star_bank import parse_star_bank_excel, parse_star_bank_pdf, select_star_stories, validate_metrics
from src.ui_components import JOB_CARD_CSS

USER_EMAIL = "demo@nomail.com"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write("Logged in as: **demo@nomail.com**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_text", "candidate_name", "active_profile",
                    "resume_analyzed", "resume_summary", "skill_gaps"):
            st.session_state.pop(key, None)
        st.rerun()

# ── Page header ────────────────────────────────────────────────────
st.markdown(JOB_CARD_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
div[data-testid="stTextArea"] textarea { background-color: #fffde7 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Quick Apply")
st.caption("Paste any job description — get a tailored resume, cover letter, and LinkedIn message instantly.")

# ── Bootstrap: profile + ATS keywords ─────────────────────────────
if "active_profile" not in st.session_state:
    with st.spinner("Loading profile…"):
        st.session_state["active_profile"] = get_active_profile(USER_EMAIL)
profile = st.session_state.get("active_profile")

if "ats_approved_keywords" not in st.session_state:
    st.session_state["ats_approved_keywords"] = get_ats_keywords(USER_EMAIL, status="approved")
approved_keywords = [k["keyword"] for k in st.session_state["ats_approved_keywords"]]

# ── Bootstrap: STAR Achievement Bank ──────────────────────────────
STAR_BANK_PATH = os.path.join(APP_DIR, "Ashu_STAR_Bank_v2.xlsx")
if "qa_star_bank" not in st.session_state:
    stories = get_star_stories(USER_EMAIL)
    if not stories:
        # First run — seed from local Excel and persist to DB
        try:
            stories = parse_star_bank_excel(STAR_BANK_PATH)
            if stories:
                save_star_stories(USER_EMAIL, stories, source_file="Ashu_STAR_Bank_v2.xlsx")
        except Exception:
            stories = []
    st.session_state["qa_star_bank"] = stories

# ── Section 1: Job Description ─────────────────────────────────────
st.subheader("1. Paste the Job Description")
jd = st.text_area(
    "Job description",
    height=250,
    placeholder="Paste the full job description here…",
    label_visibility="collapsed",
    key="qa_jd_input",
)

if st.button("🔄 Reset", help="Clear the JD and all generated outputs to start fresh"):
    for k in ("qa_jd_input", "qa_tailored_html", "qa_cl_html", "qa_dm_text",
              "qa_cl_company", "qa_cl_title"):
        st.session_state.pop(k, None)
    st.rerun()

# ── Section 2: Resume source ───────────────────────────────────────
st.subheader("2. Choose Your Resume")

col_profile, col_or, col_upload = st.columns([5, 1, 5])

with col_profile:
    if profile:
        profile_label = profile.get("candidate_name", "Saved Profile")
        if st.button(f"✅ Use saved profile resume  ({profile_label})",
                     use_container_width=True):
            st.session_state["qa_resume_source"]  = "profile"
            st.session_state["qa_resume_text"]    = profile["resume_text"]
            st.session_state["qa_candidate_name"] = profile.get("candidate_name", "Candidate")
            for k in ("qa_tailored_html", "qa_cl_html", "qa_dm_text"):
                st.session_state.pop(k, None)
    else:
        st.info("No profile saved. Go to **My Profile** to upload your resume, or upload below.")

with col_or:
    st.markdown(
        "<div style='text-align:center;padding-top:30px;font-size:15px;color:#888;'>or</div>",
        unsafe_allow_html=True,
    )

with col_upload:
    uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"],
                                     label_visibility="collapsed")
    if uploaded_file:
        last = st.session_state.get("qa_last_upload_name", "")
        if uploaded_file.name != last:
            with st.spinner("Extracting resume text…"):
                raw_text = extract_text_from_pdf(uploaded_file)
                raw_name = ask_openai(
                    f"Extract the full name from this resume. Return only the name:\n\n{raw_text[:1000]}",
                    max_tokens=50,
                ).strip().split("\n")[0]
            st.session_state["qa_resume_source"]    = "upload"
            st.session_state["qa_resume_text"]      = raw_text
            st.session_state["qa_candidate_name"]   = raw_name
            st.session_state["qa_last_upload_name"] = uploaded_file.name
            for k in ("qa_tailored_html", "qa_cl_html", "qa_dm_text"):
                st.session_state.pop(k, None)

# Resume status banner
resume_text    = st.session_state.get("qa_resume_text", "")
candidate_name = st.session_state.get("qa_candidate_name", "Candidate")
source         = st.session_state.get("qa_resume_source", "")

if resume_text:
    src_label = "from saved profile" if source == "profile" else "uploaded PDF"
    st.success(f"Resume loaded: **{candidate_name}** ({src_label})")
    if approved_keywords:
        st.caption(f"ℹ️ {len(approved_keywords)} ATS keywords will be auto-injected.")

st.markdown("---")

# ── STAR Achievement Bank expander ────────────────────────────────
with st.expander("⭐ STAR Achievement Bank", expanded=False):
    star_bank = st.session_state.get("qa_star_bank", [])
    if star_bank:
        st.caption(f"{len(star_bank)} achievement stories loaded. Best matches will be auto-woven into your resume and cover letter.")
    else:
        st.caption("No stories loaded. Upload your STAR bank below.")

    star_upload = st.file_uploader(
        "Upload a different STAR bank (.xlsx or .pdf)",
        type=["xlsx", "pdf"],
        key="qa_star_upload",
    )
    if star_upload:
        if star_upload.name != st.session_state.get("qa_last_star_upload", ""):
            with st.spinner("Parsing STAR bank…"):
                raw = star_upload.read()
                parsed = parse_star_bank_pdf(raw) if star_upload.name.endswith(".pdf") \
                    else parse_star_bank_excel(raw)
            if parsed:
                save_star_stories(USER_EMAIL, parsed, source_file=star_upload.name)
                st.session_state["qa_star_bank"] = get_star_stories(USER_EMAIL)
                st.session_state["qa_last_star_upload"] = star_upload.name
                st.success(f"Loaded {len(parsed)} stories from {star_upload.name}.")
            else:
                st.warning("Could not parse stories from the uploaded file.")

st.markdown("---")

# ── Section 3: Action buttons ──────────────────────────────────────
st.subheader("3. Generate")

ready = bool(jd.strip()) and bool(resume_text.strip())
if not ready:
    st.caption("Paste a job description and load a resume above to enable the buttons.")

btn1, btn2, btn3 = st.columns(3)

with btn1:
    resume_clicked = st.button("📄 Create Resume", use_container_width=True,
                               disabled=not ready, type="primary", key="qa_btn_resume")
with btn2:
    cl_clicked = st.button("✉️ Create Cover Letter", use_container_width=True,
                           disabled=not ready, type="primary", key="qa_btn_cl")
with btn3:
    dm_clicked = st.button("💬 Create LinkedIn Message", use_container_width=True,
                           disabled=not ready, type="primary", key="qa_btn_dm")

# ── 📄 Resume generation ───────────────────────────────────────────
if resume_clicked:
    with st.spinner("Tailoring resume to this role…"):
        try:
            with open(os.path.join(APP_DIR, "resume_template.html")) as f:
                html_template = f.read()
            _star_bank    = st.session_state.get("qa_star_bank", [])
            _star_stories = select_star_stories(jd, _star_bank) if _star_bank else []
            st.session_state["qa_selected_stories"] = _star_stories
            tailored_html = tailor_resume(
                resume_text, jd, html_template,
                approved_keywords=approved_keywords or None,
                star_stories=_star_stories or None,
            )
            st.session_state["qa_tailored_html"] = tailored_html
        except Exception as e:
            st.error(f"Resume tailoring error: {e}")

if st.session_state.get("qa_tailored_html"):
    safe_name = candidate_name.replace(" ", "_")
    pdf_name  = f"{safe_name}_Tailored_Resume.pdf"
    pdf_path  = os.path.join(APP_DIR, "output", pdf_name)
    if generate_resume_pdf(st.session_state["qa_tailored_html"], pdf_name):
        _sel = st.session_state.get("qa_selected_stories", [])
        if _sel:
            missing = validate_metrics(_sel, st.session_state["qa_tailored_html"])
            if missing:
                st.warning(
                    f"⚠️ {len(missing)} metric(s) from your STAR stories could not be verified "
                    f"verbatim in the resume. Review before sending.",
                    icon="⚠️",
                )
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Resume PDF", f.read(),
                               file_name=pdf_name, mime="application/pdf",
                               key="dl_qa_resume")
    else:
        st.error("PDF generation failed — check WeasyPrint / Pango installation.")

# ── ✉️ Cover letter generation ─────────────────────────────────────
if cl_clicked:
    with st.spinner("Extracting job details and writing cover letter…"):
        try:
            meta_raw = ask_openai(
                'Return ONLY valid JSON: {"company":"<name>","job_title":"<title>"}.\nJD:\n' + jd[:2000],
                max_tokens=80,
            )
            try:
                meta      = json.loads(meta_raw)
                company   = meta.get("company", "")
                job_title = meta.get("job_title", "")
            except Exception:
                company = job_title = ""

            with open(os.path.join(APP_DIR, "cover_letter_template.html")) as f:
                cl_template = f.read()
            _star_bank    = st.session_state.get("qa_star_bank", [])
            _star_stories = st.session_state.get("qa_selected_stories") \
                            or (select_star_stories(jd, _star_bank) if _star_bank else [])
            filled_html = generate_cover_letter(
                resume_text, jd, cl_template,
                company=company, job_title=job_title,
                star_stories=_star_stories or None,
            )
            st.session_state["qa_cl_html"]    = filled_html
            st.session_state["qa_cl_company"] = company
            st.session_state["qa_cl_title"]   = job_title
        except Exception as e:
            st.error(f"Cover letter error: {e}")

if st.session_state.get("qa_cl_html"):
    filled_html = st.session_state["qa_cl_html"]
    company     = st.session_state.get("qa_cl_company", "")
    preview     = _extract_cover_letter_text(filled_html)
    with st.expander("📝 Cover Letter Preview", expanded=True):
        st.text_area(
            "Copy-ready text (for LinkedIn messages, email, etc.)",
            value=preview, height=320, key="qa_cl_preview",
        )
    st.markdown("---")
    safe_name = candidate_name.replace(" ", "_")
    safe_co   = "".join(c for c in company if c.isalnum()) or "Company"
    pdf_name  = f"{safe_name}_CoverLetter_{safe_co}.pdf"
    pdf_path  = os.path.join(APP_DIR, "output", pdf_name)
    if generate_resume_pdf(filled_html, pdf_name):
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Cover Letter PDF", f.read(),
                               file_name=pdf_name, mime="application/pdf",
                               key="dl_qa_cl")

# ── 💬 LinkedIn DM generation ──────────────────────────────────────
if dm_clicked:
    with st.spinner("Writing LinkedIn message…"):
        try:
            dm = generate_linkedin_dm(resume_text, jd, author_name="")
            st.session_state["qa_dm_text"] = dm
        except Exception as e:
            st.error(f"LinkedIn message error: {e}")

if st.session_state.get("qa_dm_text"):
    st.markdown("**💬 LinkedIn Message**")
    st.caption("Copy and send this as a connection request or InMail.")
    st.text_area("LinkedIn Message", value=st.session_state["qa_dm_text"],
                 height=220, label_visibility="collapsed", key="qa_dm_display")
