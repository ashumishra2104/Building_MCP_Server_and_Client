import streamlit as st

st.set_page_config(page_title="AI Job Recommender", page_icon="💼", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state.get("authenticated"):
    login_page = st.Page("pages/login.py", title="Login", icon="🔓", default=True)
    pg = st.navigation([login_page], position="hidden")
else:
    ai_page          = st.Page("pages/ai_search.py",    title="AI Job Search",     icon="🔍", default=True)
    browse_page      = st.Page("pages/browse_jobs.py",  title="Browse Saved Jobs", icon="📁")
    quick_apply_page = st.Page("pages/quick_apply.py",  title="Quick Apply",       icon="⚡")
    ats_page         = st.Page("pages/ats_keywords.py", title="ATS Keywords",      icon="🎯")
    dashboard_page   = st.Page("pages/dashboard.py",    title="Dashboard",         icon="📊")
    profile_page     = st.Page("pages/my_profile.py",   title="My Profile",        icon="👤")
    pg = st.navigation([ai_page, browse_page, quick_apply_page, ats_page, dashboard_page, profile_page])

pg.run()
