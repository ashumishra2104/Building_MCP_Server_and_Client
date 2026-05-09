import streamlit as st

st.set_page_config(page_title="AI Job Recommender", page_icon="💼", layout="wide")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background:#fff;padding:30px;border-radius:16px;border:1px solid #e1e4e8;box-shadow:0 10px 25px rgba(0,0,0,0.1);'>
            <h2 style='text-align:center;color:#0077b5;margin-bottom:5px;'>🔓 Account Login</h2>
            <p style='text-align:center;color:#586069;font-size:14px;margin-bottom:25px;'>Enter your credentials to access the AI Job Recommender</p>
        </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        email    = st.text_input("📧 Email Address", placeholder="demo@nomail.com")
        password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Launch Dashboard", use_container_width=True):
            if email == "demo@nomail.com" and password == "password":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Email or Password")
