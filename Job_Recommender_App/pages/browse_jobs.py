import streamlit as st
from src.database import get_jobs_from_db, get_linkedin_posts_from_db, get_active_profile, get_applied_job_ids
from src.ui_components import JOB_CARD_CSS, render_linkedin_card, render_naukri_card, render_indeed_card, render_linkedin_post_card, normalize_hashtag_source
from src.location_utils import get_available_cities, job_matches_cities

USER_EMAIL = "demo@nomail.com"

# ── Auto-load active profile into session if resume not already set ────────────
if not st.session_state.get("resume_text"):
    if "active_profile" not in st.session_state:
        st.session_state["active_profile"] = get_active_profile(USER_EMAIL)
    prof = st.session_state.get("active_profile")
    if prof:
        st.session_state["resume_text"]    = prof.get("resume_text", "")
        st.session_state["candidate_name"] = prof.get("candidate_name", "Candidate")

# ── Load applied job IDs once per session ──────────────────────────────────────
if "applied_job_ids" not in st.session_state:
    st.session_state["applied_job_ids"] = get_applied_job_ids(USER_EMAIL)

JOBS_PER_PAGE = 10

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write("Logged in as: **demo@nomail.com**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_text", "candidate_name", "active_profile",
                    "resume_analyzed", "resume_summary", "skill_gaps"):
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

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(JOB_CARD_CSS, unsafe_allow_html=True)
st.title("📁 Browse Saved Jobs")
st.caption("All jobs loaded directly from your database — no API calls needed.")

resume_text    = st.session_state.get("resume_text", "")
candidate_name = (st.session_state.get("candidate_name", "Candidate") or "Candidate").strip().split('\n')[0]

# ── Load jobs once into session state ──────────────────────────────────────────
if "db_linkedin_jobs" not in st.session_state:
    with st.spinner("Loading LinkedIn jobs..."):
        st.session_state["db_linkedin_jobs"] = get_jobs_from_db("linkedin", limit=2000)

if "db_naukri_jobs" not in st.session_state:
    with st.spinner("Loading Naukri jobs..."):
        st.session_state["db_naukri_jobs"] = get_jobs_from_db("naukri", limit=2000)

if "db_indeed_jobs" not in st.session_state:
    with st.spinner("Loading Indeed jobs..."):
        st.session_state["db_indeed_jobs"] = get_jobs_from_db("indeed", limit=2000)

if "db_linkedin_posts" not in st.session_state:
    with st.spinner("Loading LinkedIn posts..."):
        st.session_state["db_linkedin_posts"] = get_linkedin_posts_from_db(limit=500)

linkedin_jobs   = st.session_state["db_linkedin_jobs"]
naukri_jobs     = st.session_state["db_naukri_jobs"]
indeed_jobs     = st.session_state["db_indeed_jobs"]
linkedin_posts  = st.session_state["db_linkedin_posts"]

# ── Build city list from ALL loaded jobs (self-updating) ───────────────────────
all_jobs_flat = linkedin_jobs + naukri_jobs + indeed_jobs
if "available_cities" not in st.session_state:
    st.session_state["available_cities"] = get_available_cities(all_jobs_flat)

available_cities = st.session_state["available_cities"]

# ── Filters row ───────────────────────────────────────────────────────────────
col_title, col_city = st.columns([2, 3])

with col_title:
    title_query = st.text_input("🔎 Filter by job title", placeholder="e.g. Product Manager")

with col_city:
    selected_cities = st.multiselect(
        "📍 Filter by city",
        options=available_cities,
        placeholder="Select one or more cities…",
    )

col_refresh, col_status, col_remote = st.columns([1, 3, 1])
with col_refresh:
    if st.button("🔄 Refresh DB"):
        for key in ("db_linkedin_jobs", "db_naukri_jobs", "db_indeed_jobs", "db_linkedin_posts",
                    "available_cities", "applied_job_ids"):
            st.session_state.pop(key, None)
        st.rerun()
with col_status:
    status_filter = st.radio(
        "Application status",
        options=["All", "Not Applied", "Applied"],
        horizontal=True,
        label_visibility="collapsed",
    )
with col_remote:
    remote_only = st.toggle("🌍 Remote only", key="filter_remote")

st.markdown("---")

# ── Apply filters (client-side, instant) ──────────────────────────────────────
applied_ids = st.session_state.get("applied_job_ids", set())

def _job_id(job, source):
    if source == "indeed":
        return str(job.get("id") or "")
    return str(job.get("jobId") or job.get("id") or job.get("url") or "")

def is_remote_job(job, source):
    loc = (job.get("location") or "").lower()
    if "remote" in loc:
        return True
    if source == "indeed":
        import json as _jt
        job_types = job.get("jobType") or []
        if isinstance(job_types, str):
            try:
                job_types = _jt.loads(job_types)
            except Exception:
                job_types = [job_types]
        if any("remote" in str(t).lower() for t in job_types):
            return True
    desc = (job.get("jobDescription") or job.get("description") or "").lower()
    return "remote" in desc[:500]

def apply_filters(jobs, title_field="title", source="linkedin"):
    filtered = jobs
    if title_query:
        q = title_query.lower()
        filtered = [j for j in filtered if q in (j.get(title_field) or "").lower()]
    if selected_cities:
        filtered = [j for j in filtered if job_matches_cities(j, selected_cities)]
    if remote_only:
        filtered = [j for j in filtered if is_remote_job(j, source)]
    if status_filter == "Applied":
        filtered = [j for j in filtered if _job_id(j, source) in applied_ids]
    elif status_filter == "Not Applied":
        filtered = [j for j in filtered if _job_id(j, source) not in applied_ids]
    return filtered

filtered_linkedin = apply_filters(linkedin_jobs, title_field="title",        source="linkedin")
filtered_naukri   = apply_filters(naukri_jobs,   title_field="title",        source="naukri")
filtered_indeed   = apply_filters(indeed_jobs,   title_field="positionName", source="indeed")
filtered_all      = [(j, "linkedin") for j in filtered_linkedin] + \
                    [(j, "naukri")   for j in filtered_naukri]   + \
                    [(j, "indeed")   for j in filtered_indeed]


# ── Pagination helper ──────────────────────────────────────────────────────────
def show_paginated(jobs, source, key_prefix, extra_sig=""):
    total = len(jobs)
    if total == 0:
        st.info("No jobs match your current filters.")
        return

    total_pages = max(1, (total + JOBS_PER_PAGE - 1) // JOBS_PER_PAGE)
    page_key = f"page_{key_prefix}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # Reset to page 1 when filters change
    filter_sig = f"{title_query}|{'|'.join(sorted(selected_cities))}|{extra_sig}"
    sig_key = f"sig_{key_prefix}"
    if st.session_state.get(sig_key) != filter_sig:
        st.session_state[page_key] = 1
        st.session_state[sig_key] = filter_sig

    page = max(1, min(st.session_state[page_key], total_pages))
    st.session_state[page_key] = page

    start = (page - 1) * JOBS_PER_PAGE
    end   = min(start + JOBS_PER_PAGE, total)
    page_jobs = jobs[start:end]

    st.caption(f"Showing **{start + 1}–{end}** of **{total}** jobs  •  Page {page} of {total_pages}")

    # 2-column grid
    for row in range(0, len(page_jobs), 2):
        cols = st.columns(2, gap="medium")
        for col_i in range(2):
            idx = row + col_i
            if idx >= len(page_jobs):
                break
            global_idx = start + idx
            with cols[col_i]:
                if source == "linkedin":
                    render_linkedin_card(page_jobs[idx], global_idx, resume_text, candidate_name, key_prefix=key_prefix)
                elif source == "naukri":
                    render_naukri_card(page_jobs[idx], global_idx, resume_text, candidate_name, key_prefix=key_prefix)
                elif source == "indeed":
                    render_indeed_card(page_jobs[idx], global_idx, resume_text, candidate_name, key_prefix=key_prefix)
                else:
                    job, src = page_jobs[idx]
                    if src == "linkedin":
                        render_linkedin_card(job, global_idx, resume_text, candidate_name, key_prefix=key_prefix)
                    elif src == "indeed":
                        render_indeed_card(job, global_idx, resume_text, candidate_name, key_prefix=key_prefix)
                    else:
                        render_naukri_card(job, global_idx, resume_text, candidate_name, key_prefix=key_prefix)

    # ── Pagination bar ─────────────────────────────────────────────────────────
    st.markdown("---")
    max_btns  = 5
    half      = max_btns // 2
    p_start   = max(1, page - half)
    p_end     = min(total_pages, p_start + max_btns - 1)
    p_start   = max(1, p_end - max_btns + 1)
    visible   = list(range(p_start, p_end + 1))

    btn_cols = st.columns([1.5] + [0.6] * len(visible) + [1.5])

    with btn_cols[0]:
        if st.button("◀ Prev", key=f"prev_{key_prefix}", disabled=(page <= 1)):
            st.session_state[page_key] = page - 1
            st.rerun()

    for i, p in enumerate(visible):
        with btn_cols[i + 1]:
            if p == page:
                st.markdown(
                    f"<div style='text-align:center;background:#0077b5;color:white;"
                    f"border-radius:6px;padding:5px 0;font-weight:700;'>{p}</div>",
                    unsafe_allow_html=True)
            else:
                if st.button(str(p), key=f"pg_{key_prefix}_{p}"):
                    st.session_state[page_key] = p
                    st.rerun()

    with btn_cols[-1]:
        if st.button("Next ▶", key=f"next_{key_prefix}", disabled=(page >= total_pages)):
            st.session_state[page_key] = page + 1
            st.rerun()


# ── Posts text filter ─────────────────────────────────────────────────────────
post_text_query = title_query  # reuse the title filter box

filtered_posts = linkedin_posts
if post_text_query:
    q = post_text_query.lower()
    filtered_posts = [p for p in filtered_posts if q in (p.get("text") or "").lower()
                      or q in (p.get("author_name") or "").lower()
                      or q in normalize_hashtag_source(p.get("hashtag_source") or "").lower()]
if status_filter == "Applied":
    filtered_posts = [p for p in filtered_posts if str(p.get("url") or "") in applied_ids]
elif status_filter == "Not Applied":
    filtered_posts = [p for p in filtered_posts if str(p.get("url") or "") not in applied_ids]

# ── Source tabs ────────────────────────────────────────────────────────────────
tab_naukri, tab_linkedin, tab_indeed, tab_all, tab_posts = st.tabs([
    "💼 Naukri",
    "🏢 LinkedIn",
    "🔵 Indeed",
    "🌐 All",
    "📢 Posts",
])

with tab_naukri:
    st.caption(f"{len(filtered_naukri)} jobs")
    show_paginated(filtered_naukri, "naukri", key_prefix="sn", extra_sig=str(remote_only))

with tab_linkedin:
    poster_only = st.toggle("👤 Only show jobs with poster info", key="filter_poster")
    if poster_only:
        display_linkedin = [
            j for j in filtered_linkedin
            if j.get("posterFullName") or j.get("posterProfileUrl")
        ]
    else:
        display_linkedin = filtered_linkedin
    st.caption(f"{len(display_linkedin)} jobs")
    show_paginated(display_linkedin, "linkedin", key_prefix="sl", extra_sig=f"{poster_only}|{remote_only}")

with tab_indeed:
    st.caption(f"{len(filtered_indeed)} jobs")
    show_paginated(filtered_indeed, "indeed", key_prefix="si", extra_sig=str(remote_only))

with tab_all:
    st.caption(f"{len(filtered_all)} jobs")
    show_paginated(filtered_all, "all", key_prefix="sa", extra_sig=str(remote_only))

with tab_posts:
    st.caption(f"{len(filtered_posts)} posts")
    # ── Manual trigger ─────────────────────────────────────────────────────────
    from src.job_api import fetch_linkedin_posts as _fetch_posts

    col_fetch, col_note = st.columns([1, 4])
    with col_fetch:
        if st.button("🔄 Fetch Latest Posts", use_container_width=True, key="fetch_posts_btn"):
            with st.spinner("Scraping 4 hashtag searches… this takes ~2 min"):
                saved, total = _fetch_posts(max_results=30)
            if saved > 0:
                st.success(f"✅ Saved {saved} new posts (out of {total} scraped). Refreshing…")
                st.session_state.pop("db_linkedin_posts", None)
                st.rerun()
            elif total > 0:
                st.info(f"Scraped {total} posts but all were older than 15 days or duplicates.")
            else:
                st.warning("No posts returned. Check Apify logs.")
    with col_note:
        st.caption("Fetches posts for all 4 hashtag combos via Apify. Cron also runs daily at 8 AM IST automatically.")

    # ── Keyword chips ──────────────────────────────────────────────────────────
    unique_keywords = sorted({
        normalize_hashtag_source(p.get("hashtag_source") or "")
        for p in linkedin_posts
        if p.get("hashtag_source")
    })
    if unique_keywords:
        st.markdown("**🔖 Keywords in DB:**")
        st.markdown(
            " &nbsp; ".join(
                f'<span style="background:#e8f0fe;color:#0a66c2;font-size:12px;'
                f'font-weight:600;padding:3px 10px;border-radius:12px;">{kw}</span>'
                for kw in unique_keywords
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if not filtered_posts:
        st.info("No LinkedIn posts found. Try refreshing the DB or adjusting the search filter.")
    else:
        POSTS_PER_PAGE = 10
        total_posts = len(filtered_posts)
        total_post_pages = max(1, (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)

        if "page_posts" not in st.session_state:
            st.session_state["page_posts"] = 1

        post_sig = post_text_query or ""
        if st.session_state.get("sig_posts") != post_sig:
            st.session_state["page_posts"] = 1
            st.session_state["sig_posts"] = post_sig

        post_page = max(1, min(st.session_state["page_posts"], total_post_pages))
        st.session_state["page_posts"] = post_page

        p_start = (post_page - 1) * POSTS_PER_PAGE
        p_end   = min(p_start + POSTS_PER_PAGE, total_posts)
        st.caption(f"Showing **{p_start + 1}–{p_end}** of **{total_posts}** posts  •  Page {post_page} of {total_post_pages}")

        for post in filtered_posts[p_start:p_end]:
            render_linkedin_post_card(post, resume_text, candidate_name)

        # Pagination bar
        st.markdown("---")
        max_btns = 5
        half     = max_btns // 2
        pp_start = max(1, post_page - half)
        pp_end   = min(total_post_pages, pp_start + max_btns - 1)
        pp_start = max(1, pp_end - max_btns + 1)
        visible  = list(range(pp_start, pp_end + 1))

        btn_cols = st.columns([1.5] + [0.6] * len(visible) + [1.5])
        with btn_cols[0]:
            if st.button("◀ Prev", key="prev_posts", disabled=(post_page <= 1)):
                st.session_state["page_posts"] = post_page - 1
                st.rerun()
        for i, p in enumerate(visible):
            with btn_cols[i + 1]:
                if p == post_page:
                    st.markdown(
                        f"<div style='text-align:center;background:#0a66c2;color:white;"
                        f"border-radius:6px;padding:5px 0;font-weight:700;'>{p}</div>",
                        unsafe_allow_html=True)
                else:
                    if st.button(str(p), key=f"pg_posts_{p}"):
                        st.session_state["page_posts"] = p
                        st.rerun()
        with btn_cols[-1]:
            if st.button("Next ▶", key="next_posts", disabled=(post_page >= total_post_pages)):
                st.session_state["page_posts"] = post_page + 1
                st.rerun()
