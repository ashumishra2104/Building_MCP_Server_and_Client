import streamlit as st
from src.helper import extract_text_from_pdf, ask_openai
from src.database import save_user_profile, get_active_profile, delete_user_profile, save_user_settings, get_user_settings

USER_EMAIL = "demo@nomail.com"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write(f"Logged in as: **{USER_EMAIL}**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_text", "candidate_name", "active_profile",
                    "resume_summary", "skill_gaps", "resume_analyzed"):
            st.session_state.pop(key, None)
        st.rerun()

# ── Page header ────────────────────────────────────────────────────────────────
st.title("👤 My Profile")
st.caption("Upload your resume once — it will be used automatically across all job applications.")

st.markdown("---")

# ── Load active profile ────────────────────────────────────────────────────────
if "active_profile" not in st.session_state:
    with st.spinner("Loading your profile..."):
        st.session_state["active_profile"] = get_active_profile(USER_EMAIL)

profile = st.session_state.get("active_profile")

# ── Show existing profile ──────────────────────────────────────────────────────
if profile:
    st.subheader("✅ Active Profile")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Profile Name:** {profile.get('profile_name', '—')}")
        st.markdown(f"**Candidate:** {profile.get('candidate_name', '—')}")
    with col2:
        st.markdown(f"**Email:** {profile.get('candidate_email', '—')}")
        st.markdown(f"**Phone:** {profile.get('candidate_phone', '—')}")
    with col3:
        st.markdown(f"**File:** {profile.get('raw_pdf_name', '—')}")
        updated = profile.get('updated_at', '')
        if updated:
            st.markdown(f"**Saved:** {updated[:10]}")

    with st.expander("📄 View Resume Text"):
        st.text(profile.get("resume_text", "")[:3000] + ("…" if len(profile.get("resume_text", "")) > 3000 else ""))

    st.markdown("---")

    col_del, col_new = st.columns([1, 4])
    with col_del:
        if st.button("🗑️ Delete Profile", type="secondary"):
            st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        st.warning("Are you sure? This will remove your saved profile.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete it", type="primary"):
                delete_user_profile(USER_EMAIL)
                st.session_state.pop("active_profile", None)
                st.session_state.pop("resume_text", None)
                st.session_state.pop("candidate_name", None)
                st.session_state.pop("confirm_delete", None)
                st.success("Profile deleted.")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state.pop("confirm_delete", None)
                st.rerun()

    st.markdown("### 🔄 Replace Profile")
    st.caption("Upload a new resume to overwrite the current profile.")

# ── Upload form ────────────────────────────────────────────────────────────────
with st.form("profile_upload_form", clear_on_submit=False):
    st.subheader("📤 Upload Resume")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    profile_name  = st.text_input(
        "Give this resume a name",
        placeholder="e.g. PM Resume v1, GenAI Focused, Fintech Specialist",
        max_chars=80,
    )
    submitted = st.form_submit_button("🔍 Extract & Preview", use_container_width=True)

if submitted:
    if not uploaded_file:
        st.error("Please upload a PDF file.")
    elif not profile_name.strip():
        st.error("Please give your profile a name.")
    else:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if not resume_text.strip():
            st.error("Could not extract text from this PDF. Try a different file.")
        else:
            with st.spinner("Parsing your details with AI..."):
                parse_prompt = f"""
Extract the following fields from this resume text. Return ONLY a JSON object with these exact keys:
- candidate_name
- candidate_email
- candidate_phone

If a field is not found, use null. Resume text:
{resume_text[:3000]}
"""
                raw = ask_openai(parse_prompt, max_tokens=200)
                import json, re
                parsed = {"candidate_name": None, "candidate_email": None, "candidate_phone": None}
                try:
                    match = re.search(r'\{.*?\}', raw, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group())
                except Exception:
                    pass

            st.session_state["_pending_profile"] = {
                "profile_name":   profile_name.strip(),
                "resume_text":    resume_text,
                "candidate_name": parsed.get("candidate_name"),
                "candidate_email": parsed.get("candidate_email"),
                "candidate_phone": parsed.get("candidate_phone"),
                "raw_pdf_name":   uploaded_file.name,
            }
            st.rerun()

# ── Preview & confirm save ─────────────────────────────────────────────────────
pending = st.session_state.get("_pending_profile")
if pending:
    st.markdown("---")
    st.subheader("🔎 Preview — confirm before saving")

    c1, c2, c3 = st.columns(3)
    with c1:
        new_name = st.text_input("Candidate Name", value=pending.get("candidate_name") or "", key="edit_name")
    with c2:
        new_email = st.text_input("Email", value=pending.get("candidate_email") or "", key="edit_email")
    with c3:
        new_phone = st.text_input("Phone", value=pending.get("candidate_phone") or "", key="edit_phone")

    st.caption(f"Profile name: **{pending['profile_name']}** · File: **{pending['raw_pdf_name']}**")

    with st.expander("📄 Extracted Resume Text (first 1500 chars)"):
        st.text(pending["resume_text"][:1500])

    col_save, col_cancel = st.columns([1, 5])
    with col_save:
        if st.button("💾 Save Profile", type="primary", use_container_width=True):
            with st.spinner("Saving to database..."):
                ok = save_user_profile(
                    user_email     = USER_EMAIL,
                    profile_name   = pending["profile_name"],
                    resume_text    = pending["resume_text"],
                    candidate_name = new_name.strip() or pending.get("candidate_name"),
                    candidate_email= new_email.strip() or pending.get("candidate_email"),
                    candidate_phone= new_phone.strip() or pending.get("candidate_phone"),
                    raw_pdf_name   = pending["raw_pdf_name"],
                )
            if ok:
                st.session_state.pop("_pending_profile", None)
                st.session_state.pop("active_profile", None)  # force reload
                st.session_state["resume_text"]    = pending["resume_text"]
                st.session_state["candidate_name"] = new_name.strip() or pending.get("candidate_name") or "Candidate"
                st.success("✅ Profile saved! It will be used automatically in Browse Jobs.")
                st.rerun()
            else:
                st.error("Failed to save. Check Supabase connection.")
    with col_cancel:
        if st.button("✖ Cancel"):
            st.session_state.pop("_pending_profile", None)
            st.rerun()

# ── Scraper Settings ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚙️ Scraper Settings")
st.caption("Control how many jobs are fetched per Apify search run.")

if "scraper_settings" not in st.session_state:
    st.session_state["scraper_settings"] = get_user_settings(USER_EMAIL)

settings = st.session_state["scraper_settings"]

linkedin_rows = st.slider(
    "LinkedIn — jobs per search title (× 3 titles)",
    min_value=20, max_value=300,
    value=settings.get("linkedin_rows", 100),
    step=10,
    key="slider_linkedin",
)
naukri_rows = st.slider(
    "Naukri — total jobs",
    min_value=50, max_value=500,
    value=settings.get("naukri_rows", 150),
    step=10,
    key="slider_naukri",
)
indeed_rows = st.slider(
    "Indeed — jobs per search title (× 3 titles)",
    min_value=20, max_value=200,
    value=settings.get("indeed_rows", 75),
    step=5,
    key="slider_indeed",
)

st.caption(
    f"Current totals: LinkedIn up to **{linkedin_rows * 3}** · "
    f"Naukri **{naukri_rows}** · "
    f"Indeed up to **{indeed_rows * 3}** unique jobs."
)

if st.button("💾 Save Settings", type="primary"):
    if save_user_settings(USER_EMAIL, linkedin_rows, naukri_rows, indeed_rows):
        st.session_state["scraper_settings"] = {
            "linkedin_rows": linkedin_rows,
            "naukri_rows":   naukri_rows,
            "indeed_rows":   indeed_rows,
        }
        st.success("Settings saved!")
    else:
        st.error("Failed to save settings.")

# ── Outreach Signature ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("✍️ Outreach Signature")
st.caption("Appended to LinkedIn DMs generated for job posters.")

current_website = (profile or {}).get("candidate_website", "") if profile else ""
current_github  = (profile or {}).get("candidate_github",  "") if profile else ""

candidate_website = st.text_input(
    "Website / Portfolio URL",
    value=current_website,
    placeholder="https://yoursite.com",
    key="sig_website",
)
candidate_github = st.text_input(
    "GitHub URL",
    value=current_github,
    placeholder="https://github.com/yourusername",
    key="sig_github",
)

if st.button("💾 Save Signature", type="primary", key="save_sig_btn"):
    if not profile:
        st.warning("Save a profile first before adding a signature.")
    else:
        with st.spinner("Saving…"):
            ok = save_user_profile(
                USER_EMAIL,
                profile["profile_name"],
                profile["resume_text"],
                profile.get("candidate_name"),
                profile.get("candidate_email"),
                profile.get("candidate_phone"),
                profile.get("raw_pdf_name"),
                candidate_website=candidate_website,
                candidate_github=candidate_github,
            )
        if ok:
            st.session_state["active_profile"]["candidate_website"] = candidate_website
            st.session_state["active_profile"]["candidate_github"]  = candidate_github
            st.success("Signature saved!")
        else:
            st.error("Failed to save. Check Supabase connection.")
