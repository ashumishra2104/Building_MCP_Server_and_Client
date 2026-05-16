import streamlit as st
from src.database import (
    get_jobs_from_db,
    get_last_extraction_time,
    save_ats_keywords,
    get_ats_keywords,
    update_keyword_status,
    auto_classify_keywords,
    bulk_update_keyword_status,
)
from src.helper import extract_ats_keywords
from src.ui_components import JOB_CARD_CSS

USER_EMAIL = "demo@nomail.com"

CATEGORY_LABELS = {
    "power_verb":      "⚡ Power Verbs",
    "technical_skill": "🛠️ Technical Skills",
    "domain_keyword":  "🎯 Domain Keywords",
    "ats_phrase":      "💬 ATS Phrases",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write("Logged in as: **demo@nomail.com**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_text", "candidate_name", "active_profile",
                    "resume_analyzed", "resume_summary", "skill_gaps"):
            st.session_state.pop(key, None)
        st.rerun()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(JOB_CARD_CSS, unsafe_allow_html=True)
st.title("🎯 ATS Keyword Intelligence")
st.caption("Extract high-value keywords from all stored job descriptions and auto-inject them into your tailored resumes.")

tab_extract, tab_review, tab_approved = st.tabs(["⚡ Extract", "📋 Review", "✅ My Keywords"])


# ── Tab 1: Extract ─────────────────────────────────────────────────────────────
with tab_extract:
    st.subheader("Extract Keywords from Job Descriptions")

    # DB stats
    try:
        from src.database import supabase as sb
        if sb:
            l_count = sb.table("linkedin_jobs_v2").select("*", count="exact").limit(1).execute().count or 0
            n_count = sb.table("naukri_jobs_v2").select("*", count="exact").limit(1).execute().count or 0
            i_count = sb.table("indeed_jobs").select("*", count="exact").limit(1).execute().count or 0
        else:
            l_count = n_count = i_count = 0
    except Exception:
        l_count = n_count = i_count = 0

    total_jds = l_count + n_count + i_count

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("LinkedIn JDs", l_count)
    col2.metric("Naukri JDs", n_count)
    col3.metric("Indeed JDs", i_count)
    col4.metric("Total", total_jds)

    last_run = get_last_extraction_time(USER_EMAIL)
    if last_run:
        st.info(f"Last extraction: **{last_run[:19].replace('T', ' ')} UTC**  —  Only JDs fetched after this will be processed.")
    else:
        st.info("No previous extraction found. The first run will process all JDs in the database.")

    force_all = st.checkbox(
        "🔁 Re-extract all JDs (ignore last extraction date)",
        value=False,
        help="Use this to force a full re-extraction — useful when Supabase table is newly created or you want fresh results.",
    )

    st.markdown("---")

    if st.button("🔄 Extract New Keywords", type="primary", use_container_width=False):

        # ── Stage 1: Load JDs ────────────────────────────────────────────────
        bar  = st.progress(0,  text="📂  Stage 1 / 4 — Loading job descriptions from database…")
        info = st.empty()

        linkedin_jobs = get_jobs_from_db("linkedin", limit=5000)
        bar.progress(5, text="📂  Stage 1 / 4 — Loading Naukri jobs…")
        naukri_jobs   = get_jobs_from_db("naukri",   limit=5000)
        bar.progress(10, text="📂  Stage 1 / 4 — Loading Indeed jobs…")
        indeed_jobs   = get_jobs_from_db("indeed",   limit=5000)

        # ── Stage 2: Filter & prepare ────────────────────────────────────────
        bar.progress(15, text="🔍  Stage 2 / 4 — Filtering new JDs and preparing batches…")

        if last_run and not force_all:
            def _is_new(job):
                ft = job.get("_fetched_at") or job.get("fetched_at") or ""
                return str(ft) > last_run
            linkedin_jobs = [j for j in linkedin_jobs if _is_new(j)]
            naukri_jobs   = [j for j in naukri_jobs   if _is_new(j)]
            indeed_jobs   = [j for j in indeed_jobs   if _is_new(j)]

        jd_texts = []
        for job in linkedin_jobs + naukri_jobs:
            text = job.get("jobDescription") or job.get("description") or ""
            if text and text.strip():
                jd_texts.append(text.strip())
        for job in indeed_jobs:
            text = job.get("description") or ""
            if text and text.strip():
                jd_texts.append(text.strip())

        new_jd_count  = len(jd_texts)
        import math
        total_batches = max(1, math.ceil(new_jd_count / 15))
        bar.progress(20, text=f"🔍  Stage 2 / 4 — {new_jd_count} JDs ready → {total_batches} batches (5 parallel workers)")

        if new_jd_count == 0:
            bar.empty()
            st.warning("No new job descriptions found since the last extraction. Fetch fresh jobs first, then re-extract.")
        else:
            info.info(f"**{new_jd_count}** JDs → **{total_batches}** batches → 5 parallel workers → gpt-4.1")

            # ── Stage 3: Extract (parallel) ──────────────────────────────────
            # Map batch completion (0→total_batches) onto progress 20→85
            EXTRACT_START = 20
            EXTRACT_END   = 85

            def _on_batch_done(completed, total):
                pct = EXTRACT_START + int((completed / total) * (EXTRACT_END - EXTRACT_START))
                bar.progress(
                    pct,
                    text=(
                        f"🤖  Stage 3 / 4 — Extracting keywords: "
                        f"batch **{completed} / {total}** complete  "
                        f"({'~' + str(int((total - completed) * 8 / 5)) + 's left' if completed < total else 'finishing…'})"
                    ),
                )

            keywords_by_category = extract_ats_keywords(jd_texts, progress_callback=_on_batch_done)

            # ── Stage 4: Save ────────────────────────────────────────────────
            bar.progress(88, text="💾  Stage 4 / 4 — Saving keywords to database…")
            saved_count, sb_error = save_ats_keywords(USER_EMAIL, keywords_by_category)
            bar.progress(100, text="✅  Done! All stages complete.")

            if sb_error:
                st.warning(
                    f"⚠️ **Supabase save failed** (keywords saved to local DB instead): `{sb_error}`  \n"
                    "👉 Likely fix: go to Supabase → Table Editor → `ats_keywords` → "
                    "**Disable RLS** (or add an insert policy for the anon key)."
                )

            total_unique = sum(len(v) for v in keywords_by_category.values())
            info.success(
                f"✅ Extracted **{total_unique}** unique keywords from **{new_jd_count}** job descriptions "
                f"across **{total_batches}** batches. Head to **📋 Review** to approve them."
            )

            st.session_state.pop("ats_all_keywords", None)
            st.session_state.pop("ats_approved_keywords", None)
            st.rerun()


# ── Tab 2: Review ──────────────────────────────────────────────────────────────
with tab_review:
    st.subheader("Review & Approve Keywords")

    if "ats_all_keywords" not in st.session_state:
        st.session_state["ats_all_keywords"] = get_ats_keywords(USER_EMAIL)

    all_kws = st.session_state["ats_all_keywords"]

    if not all_kws:
        st.info("No keywords yet. Run extraction in the ⚡ Extract tab first.")
    else:
        total_kws    = len(all_kws)
        approved_cnt = sum(1 for k in all_kws if k["status"] == "approved")
        pending_cnt  = sum(1 for k in all_kws if k["status"] == "pending")
        rejected_cnt = sum(1 for k in all_kws if k["status"] == "rejected")

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total", total_kws)
        mc2.metric("Pending", pending_cnt)
        mc3.metric("Approved", approved_cnt)
        mc4.metric("Rejected", rejected_cnt)

        st.markdown("---")

        # ── Auto-classify panel ───────────────────────────────────────────────
        with st.expander("⚡ Auto-classify by Frequency", expanded=True):
            st.caption("Approve all keywords above the threshold; reject the rest. Existing approved/rejected statuses are overwritten.")
            ac_col1, ac_col2 = st.columns([2, 1])
            with ac_col1:
                freq_threshold = st.number_input(
                    "Minimum frequency to auto-approve",
                    min_value=1, max_value=100, value=5, step=1,
                    help="Keywords appearing in ≥ this many batches are approved; all others are rejected.",
                )
            with ac_col2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("⚡ Auto-classify", type="primary", use_container_width=True):
                    with st.spinner("Classifying…"):
                        app_n, rej_n = auto_classify_keywords(USER_EMAIL, min_frequency=freq_threshold)
                    st.success(f"Done — **{app_n} approved**, **{rej_n} rejected** (threshold ≥ {freq_threshold})")
                    st.session_state.pop("ats_all_keywords", None)
                    st.session_state.pop("ats_approved_keywords", None)
                    st.session_state.pop("ats_selected", None)
                    st.rerun()

        st.markdown("---")

        # ── Bulk actions bar ──────────────────────────────────────────────────
        if "ats_selected" not in st.session_state:
            st.session_state["ats_selected"] = set()

        selected: set = st.session_state["ats_selected"]
        n_selected = len(selected)

        bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 1, 1])
        with bulk_col1:
            st.caption(f"**{n_selected}** keyword(s) selected")
        with bulk_col2:
            if st.button(f"✅ Approve Selected ({n_selected})", disabled=(n_selected == 0), use_container_width=True, type="primary"):
                bulk_update_keyword_status(USER_EMAIL, list(selected), "approved")
                st.session_state.pop("ats_all_keywords", None)
                st.session_state.pop("ats_approved_keywords", None)
                st.session_state["ats_selected"] = set()
                st.rerun()
        with bulk_col3:
            if st.button(f"❌ Reject Selected ({n_selected})", disabled=(n_selected == 0), use_container_width=True):
                bulk_update_keyword_status(USER_EMAIL, list(selected), "rejected")
                st.session_state.pop("ats_all_keywords", None)
                st.session_state.pop("ats_approved_keywords", None)
                st.session_state["ats_selected"] = set()
                st.rerun()

        st.markdown("---")

        # Filter
        status_filter = st.radio(
            "Show", ["All", "Pending", "Approved", "Rejected"],
            horizontal=True, label_visibility="collapsed"
        )
        filter_map = {"All": None, "Pending": "pending", "Approved": "approved", "Rejected": "rejected"}
        filtered_status = filter_map[status_filter]

        filtered_kws = [k for k in all_kws if filtered_status is None or k["status"] == filtered_status]

        # Group by category
        from collections import defaultdict
        by_cat = defaultdict(list)
        for kw in filtered_kws:
            by_cat[kw["category"]].append(kw)

        for category, label in CATEGORY_LABELS.items():
            kws_in_cat = by_cat.get(category, [])
            if not kws_in_cat:
                continue
            with st.expander(f"{label}  ({len(kws_in_cat)} keywords)", expanded=(category == "power_verb")):
                # Select All / Deselect All for this category
                cat_ids = {kw["keyword"] for kw in kws_in_cat}
                all_selected = cat_ids.issubset(selected)
                sa_col, _ = st.columns([2, 5])
                with sa_col:
                    if st.button(
                        "Deselect All" if all_selected else "Select All",
                        key=f"sa_{category}",
                        use_container_width=True,
                    ):
                        if all_selected:
                            st.session_state["ats_selected"] -= cat_ids
                        else:
                            st.session_state["ats_selected"] |= cat_ids
                        st.rerun()

                for kw in kws_in_cat:
                    col_cb, col_kw, col_freq, col_approve, col_reject = st.columns([0.5, 3, 1, 1, 1])
                    with col_cb:
                        checked = st.checkbox(
                            "", value=(kw["keyword"] in selected),
                            key=f"cb_{kw['id']}",
                            label_visibility="collapsed",
                        )
                        if checked:
                            st.session_state["ats_selected"].add(kw["keyword"])
                        else:
                            st.session_state["ats_selected"].discard(kw["keyword"])
                    with col_kw:
                        status_icon = {"approved": "✅", "rejected": "❌", "pending": "○"}.get(kw["status"], "○")
                        st.markdown(f"{status_icon} **{kw['keyword']}**")
                    with col_freq:
                        st.caption(f"freq: {kw['frequency']}")
                    with col_approve:
                        if kw["status"] != "approved":
                            if st.button("Approve", key=f"app_{kw['id']}", type="primary", use_container_width=True):
                                update_keyword_status(USER_EMAIL, kw["keyword"], "approved")
                                st.session_state.pop("ats_all_keywords", None)
                                st.session_state.pop("ats_approved_keywords", None)
                                st.rerun()
                    with col_reject:
                        if kw["status"] != "rejected":
                            if st.button("Reject", key=f"rej_{kw['id']}", use_container_width=True):
                                update_keyword_status(USER_EMAIL, kw["keyword"], "rejected")
                                st.session_state.pop("ats_all_keywords", None)
                                st.session_state.pop("ats_approved_keywords", None)
                                st.rerun()


# ── Tab 3: My Approved Keywords ────────────────────────────────────────────────
with tab_approved:
    st.subheader("My Approved Keywords")
    st.caption("These are auto-injected into every Resume Tailoring call. The AI only uses keywords supported by your actual experience.")

    if "ats_approved_keywords" not in st.session_state:
        st.session_state["ats_approved_keywords"] = get_ats_keywords(USER_EMAIL, status="approved")

    approved_kws = st.session_state["ats_approved_keywords"]

    if not approved_kws:
        st.info("No approved keywords yet. Go to **📋 Review** to approve keywords.")
    else:
        st.success(f"**{len(approved_kws)} keywords** will be auto-injected into your next tailored resume.")
        st.markdown("---")

        from collections import defaultdict
        by_cat = defaultdict(list)
        for kw in approved_kws:
            by_cat[kw["category"]].append(kw)

        for category, label in CATEGORY_LABELS.items():
            kws_in_cat = by_cat.get(category, [])
            if not kws_in_cat:
                continue
            st.markdown(f"**{label}**")
            # Render as chips
            chips_html = " &nbsp; ".join(
                f'<span style="background:#dcfce7;color:#166534;font-size:13px;font-weight:600;'
                f'padding:4px 12px;border-radius:14px;border:1px solid #86efac;">'
                f'{kw["keyword"]}</span>'
                for kw in kws_in_cat
            )
            st.markdown(chips_html, unsafe_allow_html=True)

            # Remove buttons in a collapsed expander to keep the UI clean
            with st.expander("Remove keywords from this category"):
                for kw in kws_in_cat:
                    col_name, col_btn = st.columns([4, 1])
                    with col_name:
                        st.markdown(f"**{kw['keyword']}**  `freq: {kw['frequency']}`")
                    with col_btn:
                        if st.button("🗑", key=f"rm_{kw['id']}", use_container_width=True):
                            update_keyword_status(USER_EMAIL, kw["keyword"], "pending")
                            st.session_state.pop("ats_approved_keywords", None)
                            st.session_state.pop("ats_all_keywords", None)
                            st.rerun()
            st.markdown("")
