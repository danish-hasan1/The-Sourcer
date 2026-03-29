"""
pages/01_Login.py — Sign In
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.auth import sign_in, load_user_session
from utils.helpers import inject_global_css

st.set_page_config(page_title="Sign In — The Sourcer", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")
inject_global_css()

if "user" in st.session_state and st.session_state.user:
    st.switch_page("pages/03_Dashboard.py")

st.markdown("""
<style>
.auth-container { max-width: 440px; margin: 3rem auto; }
.auth-title { font-size: 1.6rem; font-weight: 800; color: #F1F5F9; margin-bottom: 0.25rem; }
.auth-sub { color: #64748B; font-size: 0.88rem; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# Brand
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align:center; margin-bottom: 2rem; margin-top: 2rem;">
        <div style="font-size:1.6rem; font-weight:800; color:#14B8A6; letter-spacing:-0.02em;">
            The<span style="color:#F59E0B;">Sourcer</span>
        </div>
        <div style="font-size:0.75rem; color:#475569; letter-spacing:0.08em; text-transform:uppercase;">
            AI Talent Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-sub">Sign in to continue sourcing</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email address", placeholder="you@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Signing in..."):
                    result = sign_in(email, password)
                if result["success"]:
                    st.session_state.user = result["user"]
                    st.session_state.session = result["session"]
                    load_user_session(result["user"].id)
                    st.success("Signed in! Redirecting...")
                    st.rerun()
                else:
                    st.error(result["error"])

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Create account", use_container_width=True):
            st.switch_page("pages/02_Signup.py")
    with col_b:
        if st.button("← Back to home", use_container_width=True):
            st.switch_page("app.py")
