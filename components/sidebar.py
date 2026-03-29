"""
components/sidebar.py
Consistent sidebar navigation for all authenticated pages.
"""
import streamlit as st
from core.auth import sign_out, is_admin
from utils.helpers import inject_global_css


def render_sidebar():
    """Render the main navigation sidebar."""
    inject_global_css()

    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="padding:1rem 0 0.5rem;">
            <div style="font-size:1.3rem; font-weight:800; color:#14B8A6; letter-spacing:-0.02em;">
                The<span style="color:#F59E0B;">Sourcer</span>
            </div>
            <div style="font-size:0.68rem; color:#475569; letter-spacing:0.1em; text-transform:uppercase; margin-top:2px;">
                AI Talent Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Profile snippet
        profile = st.session_state.get("profile") or {}
        name = (profile.get("full_name") or "Recruiter").strip() or "Recruiter"
        role = profile.get("role", "user")
        company = profile.get("company") or ""

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; padding:8px 0; margin-bottom:8px;">
            <div style="width:36px; height:36px; border-radius:50%;
                        background:linear-gradient(135deg,#0D9488,#F59E0B);
                        display:flex; align-items:center; justify-content:center;
                        font-weight:800; color:white; font-size:14px; flex-shrink:0;">
                {name[0].upper()}
            </div>
            <div style="min-width:0; overflow:hidden;">
                <div style="font-size:13px; font-weight:600; color:#F1F5F9;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{name}</div>
                <div style="font-size:11px; color:#475569; text-transform:capitalize;">
                    {company or role}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── MAIN NAV ──────────────────────────────────────────────────────────
        _nav_label("MAIN")

        _nav_btn("🏠  Dashboard",          "pages/03_Dashboard.py",       "nav_dash")
        _nav_btn("🔍  New Search",          "pages/04_New_Search.py",      "nav_search")
        _nav_btn("👥  Candidate Database",  "pages/06_Candidate_Database.py", "nav_cands")
        _nav_btn("🗂️  Saved Searches",     "pages/07_Saved_Searches.py",  "nav_saved")

        st.markdown("---")

        # ── TOOLS ─────────────────────────────────────────────────────────────
        _nav_label("TOOLS")

        _nav_btn("🔤  Boolean Builder",    "pages/11_Boolean_Builder.py", "nav_bool")
        _nav_btn("✉️  Outreach",           "pages/08_Outreach.py",        "nav_outreach")

        st.markdown("---")

        # ── ACCOUNT ───────────────────────────────────────────────────────────
        _nav_label("ACCOUNT")

        _nav_btn("⚙️  Settings",           "pages/09_Settings.py",        "nav_settings")

        if is_admin():
            _nav_btn("🛡️  Admin Panel",    "pages/10_Admin.py",           "nav_admin")

        st.markdown("---")

        # Sign out
        if st.button("↩  Sign Out", use_container_width=True, key="nav_signout"):
            sign_out()

        # Version tag
        st.markdown("""
        <div style="font-size:0.65rem; color:#1E293B; text-align:center; margin-top:8px;">
            The Sourcer v1.0 · MVP
        </div>
        """, unsafe_allow_html=True)


def _nav_btn(label: str, page: str, key: str):
    """Render a sidebar navigation button."""
    if st.button(label, use_container_width=True, key=key):
        st.switch_page(page)


def _nav_label(text: str):
    st.markdown(
        f'<div style="font-size:10px; color:#334155; text-transform:uppercase; '
        f'letter-spacing:0.1em; font-weight:700; margin-bottom:4px;">{text}</div>',
        unsafe_allow_html=True,
    )
