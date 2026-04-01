import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/00_Confirm_Email.py — Email Confirmation Landing
Handles Supabase's email confirmation redirect.
"""
import streamlit as st
from utils.helpers import inject_global_css, hide_sidebar_on_auth, auth_brand

st.set_page_config(
    page_title="Email Confirmed — The Sourcer",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_global_css()
hide_sidebar_on_auth()

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse 70% 50% at 50% 0%, rgba(13,148,136,0.12) 0%, transparent 55%),
        #0F172A !important;
}
</style>
""", unsafe_allow_html=True)

auth_brand()

# Check for Supabase confirmation token in URL params
params = st.query_params
token_hash = params.get("token_hash","")
token_type = params.get("type","")
error_desc = params.get("error_description","")

if error_desc:
    st.error(f"⚠️ Confirmation failed: {error_desc}")
    st.markdown("The confirmation link may have expired. Please try signing up again.")
    if st.button("← Back to Signup"):
        st.switch_page("pages/02_Signup.py")

elif token_hash or token_type == "signup":
    st.markdown("""
    <div style="text-align:center; padding:2rem 0;">
        <div style="font-size:3rem; margin-bottom:1rem;">✅</div>
        <div style="font-size:1.5rem; font-weight:800; color:#F1F5F9; margin-bottom:8px;">
            Email Confirmed!
        </div>
        <div style="color:#64748B; font-size:0.9rem;">
            Your account is ready. Sign in to start sourcing.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("→ Sign In Now", type="primary", use_container_width=False):
        st.switch_page("pages/01_Login.py")

else:
    # No token — direct visit
    st.markdown("""
    <div style="text-align:center; padding:2rem 0;">
        <div style="font-size:3rem; margin-bottom:1rem;">📧</div>
        <div style="font-size:1.4rem; font-weight:800; color:#F1F5F9; margin-bottom:8px;">
            Check Your Email
        </div>
        <div style="color:#64748B; font-size:0.88rem; max-width:380px; margin:0 auto; line-height:1.6;">
            We sent a confirmation link to your email address.
            Click it to activate your account, then come back to sign in.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Signup", use_container_width=True):
            st.switch_page("pages/02_Signup.py")
    with col2:
        if st.button("Sign In →", use_container_width=True, type="primary"):
            st.switch_page("pages/01_Login.py")

    st.markdown("---")
    with st.expander("⚙️ Admin: disable email confirmation for instant signup"):
        st.markdown("""
**Supabase Dashboard → Authentication → Settings**  
→ Turn **OFF** "Enable email confirmations" → Save

Users will be able to sign up and log in immediately without confirming.
        """)
