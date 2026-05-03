import streamlit as st
from src.database import get_jobs_from_db, get_linkedin_posts_from_db
from src.ui_components import JOB_CARD_CSS, render_linkedin_card, render_naukri_card, render_indeed_card, render_linkedin_post_card
from src.location_utils import get_available_cities, job_matches_cities

JOBS_PER_PAGE = 10

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
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
        st.session_state["db_linkedin_jobs"] = get_jobs_from_db("linkedin", limit=500)

if "db_naukri_jobs" not in st.session_state:
    with st.spinner("Loading Naukri jobs..."):
        st.session_state["db_naukri_jobs"] = get_jobs_from_db("naukri", limit=500)

if "db_indeed_jobs" not in st.session_state:
    with st.spinner("Loading Indeed jobs..."):
        st.session_state["db_indeed_jobs"] = get_jobs_from_db("indeed", limit=500)

if "db_linkedin_posts" not in st.session_state:
    with st.spinner("Loading LinkedIn posts..."):
        st.session_state["db_linkedin_posts"] = get_linkedin_posts_from_db(limit=200)

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

col_refresh, col_clear = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh DB"):
        for key in ("db_linkedin_jobs", "db_naukri_jobs", "db_indeed_jobs", "db_linkedin_posts", "available_cities"):
            st.session_state.pop(key, None)
        st.rerun()
with col_clear:
    if selected_cities or title_query:
        st.caption(f"Showing results filtered by: "
                   + (f"title=`{title_query}` " if title_query else "")
                   + (f"cities=`{', '.join(selected_cities)}`" if selected_cities else ""))

st.markdown("---")

# ── Apply filters (client-side, instant) ──────────────────────────────────────
def apply_filters(jobs, title_field='title'):
    filtered = jobs
    if title_query:
        q = title_query.lower()
        filtered = [j for j in filtered if q in (j.get(title_field) or '').lower()]
    if selected_cities:
        filtered = [j for j in filtered if job_matches_cities(j, selected_cities)]
    return filtered

filtered_linkedin = apply_filters(linkedin_jobs, title_field='title')
filtered_naukri   = apply_filters(naukri_jobs,   title_field='title')
filtered_indeed   = apply_filters(indeed_jobs,   title_field='positionName')
filtered_all      = [(j, "linkedin") for j in filtered_linkedin] + \
                    [(j, "naukri")   for j in filtered_naukri]   + \
                    [(j, "indeed")   for j in filtered_indeed]


# ── Pagination helper ──────────────────────────────────────────────────────────
def show_paginated(jobs, source, key_prefix):
    total = len(jobs)
    if total == 0:
        st.info("No jobs match your current filters.")
        return

    total_pages = max(1, (total + JOBS_PER_PAGE - 1) // JOBS_PER_PAGE)
    page_key = f"page_{key_prefix}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # Reset to page 1 when filters change
    filter_sig = f"{title_query}|{'|'.join(sorted(selected_cities))}"
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


# ── Posts text filter (separate from job title filter) ────────────────────────
post_text_query = title_query  # reuse the title filter box for post text search

filtered_posts = linkedin_posts
if post_text_query:
    q = post_text_query.lower()
    filtered_posts = [p for p in linkedin_posts if q in (p.get("text") or "").lower()
                      or q in (p.get("author_name") or "").lower()]

# ── Source tabs ────────────────────────────────────────────────────────────────
tab_naukri, tab_linkedin, tab_indeed, tab_all, tab_posts = st.tabs([
    f"💼 Naukri  ({len(filtered_naukri)})",
    f"🏢 LinkedIn  ({len(filtered_linkedin)})",
    f"🔵 Indeed  ({len(filtered_indeed)})",
    f"🌐 All  ({len(filtered_all)})",
    f"📢 Posts  ({len(filtered_posts)})",
])

with tab_naukri:
    show_paginated(filtered_naukri, "naukri", key_prefix="sn")

with tab_linkedin:
    show_paginated(filtered_linkedin, "linkedin", key_prefix="sl")

with tab_indeed:
    show_paginated(filtered_indeed, "indeed", key_prefix="si")

with tab_all:
    show_paginated(filtered_all, "all", key_prefix="sa")

with tab_posts:
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
            render_linkedin_post_card(post)

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
