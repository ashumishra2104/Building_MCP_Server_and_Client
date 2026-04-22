import streamlit as st

st.set_page_config(page_title="AI Job Recommender", page_icon="💼", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

ai_page     = st.Page("pages/ai_search.py",  title="AI Job Search",     icon="🔍", default=True)
browse_page = st.Page("pages/browse_jobs.py", title="Browse Saved Jobs", icon="📁")

pg = st.navigation([ai_page, browse_page])
pg.run()
