import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.auth import sign_in, load_user_session
from utils.helpers import inject_global_css, hide_sidebar_on_auth, auth_brand

st.set_page_config(
    page_title="Sign In — The Sourcer",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_global_css()
hide_sidebar_on_auth()

if st.session_state.get("user"):
    st.switch_page("pages/03_Dashboard.py")

# ── Background glow ────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse 70% 50% at 50% 0%, rgba(13,148,136,0.12) 0%, transparent 55%),
        #0F172A !important;
}
div[data-testid="stVerticalBlock"] > div:first-child { margin-top: 3rem; }
</style>
""", unsafe_allow_html=True)

# ── Brand ──────────────────────────────────────────────────────────────────────
auth_brand()

# ── Card ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="auth-title">Welcome back</div>', unsafe_allow_html=True)
st.markdown('<div class="auth-subtitle">Sign in to continue sourcing</div>', unsafe_allow_html=True)

# ── Form ───────────────────────────────────────────────────────────────────────
with st.form("login_form", clear_on_submit=False):
    email    = st.text_input("Email address", placeholder="you@company.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

if submitted:
    if not email.strip() or not password.strip():
        st.error("Please enter both email and password.")
    else:
        with st.spinner("Signing in..."):
            result = sign_in(email.strip(), password)
        if result["success"]:
            st.session_state.user    = result["user"]
            st.session_state.session = result["session"]
            load_user_session(result["user"].id)
            st.switch_page("pages/03_Dashboard.py")
        else:
            st.error(result["error"])

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Footer links ───────────────────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-top:0.5rem;">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("← Home", use_container_width=True):
        st.switch_page("app.py")
with col2:
    st.markdown('<div style="height:38px"></div>', unsafe_allow_html=True)
with col3:
    if st.button("Create account →", use_container_width=True):
        st.switch_page("pages/02_Signup.py")
st.markdown('</div>', unsafe_allow_html=True)
