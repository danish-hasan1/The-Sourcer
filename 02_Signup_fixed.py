"""
pages/02_Signup.py — Create Account
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.auth import sign_up, sign_in, load_user_session
from utils.helpers import inject_global_css

st.set_page_config(
    page_title="Create Account — The Sourcer",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_global_css()

if st.session_state.get("user"):
    st.switch_page("pages/03_Dashboard.py")

st.markdown("""
<div style="text-align:center; margin: 2.5rem 0 2rem;">
    <div style="font-size:1.8rem; font-weight:800; color:#14B8A6; letter-spacing:-0.03em;">
        The<span style="color:#F59E0B;">Sourcer</span>
    </div>
    <div style="font-size:0.72rem; color:#475569; letter-spacing:0.1em; text-transform:uppercase; margin-top:4px;">
        AI Talent Intelligence
    </div>
</div>
<div style="font-size:1.5rem; font-weight:800; color:#F1F5F9; margin-bottom:4px;">Create your account</div>
<div style="color:#64748B; font-size:0.88rem; margin-bottom:1.5rem;">Free to start. Your API keys. Full control.</div>
""", unsafe_allow_html=True)

with st.form("signup_form", clear_on_submit=False):
    full_name  = st.text_input("Full name", placeholder="Jane Smith")
    email      = st.text_input("Work email", placeholder="you@company.com")
    password   = st.text_input("Password", type="password", placeholder="At least 8 characters")
    confirm_pw = st.text_input("Confirm password", type="password", placeholder="Repeat password")
    st.markdown('<div style="font-size:0.75rem; color:#475569; margin:8px 0 4px;">By signing up you confirm that all candidate sourcing will be done using publicly available information in compliance with applicable platform terms.</div>', unsafe_allow_html=True)
    submitted  = st.form_submit_button("Create Account →", use_container_width=True, type="primary")

if submitted:
    errors = []
    if not full_name.strip():
        errors.append("Full name is required.")
    if not email.strip() or "@" not in email:
        errors.append("A valid email address is required.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != confirm_pw:
        errors.append("Passwords do not match.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Creating your account..."):
            result = sign_up(email.strip(), password, full_name.strip())

        if result["success"]:
            with st.spinner("Signing you in..."):
                login_result = sign_in(email.strip(), password)

            if login_result["success"]:
                st.session_state.user    = login_result["user"]
                st.session_state.session = login_result["session"]
                load_user_session(login_result["user"].id)
                st.success("🎉 Account created! Welcome to The Sourcer.")
                st.switch_page("pages/03_Dashboard.py")
            else:
                st.success("✅ Account created! Please check your email to confirm, then sign in.")
                if st.button("→ Go to Sign In", type="primary"):
                    st.switch_page("pages/01_Login.py")
        else:
            st.error(result["error"])
            if "database" in (result.get("error") or "").lower():
                st.info("Admin: Run signup_fix.sql in Supabase SQL Editor to fix this.")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("Already have an account?", use_container_width=True):
        st.switch_page("pages/01_Login.py")
with col2:
    if st.button("← Home", use_container_width=True):
        st.switch_page("app.py")

with st.expander("⚙️ Admin tip: disable email confirmation for instant signup"):
    st.markdown("Supabase Dashboard → Authentication → Settings → Turn OFF 'Enable email confirmations'")
