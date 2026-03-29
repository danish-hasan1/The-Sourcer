"""
components/sidebar.py — Custom navigation sidebar for authenticated pages.
"""
import streamlit as st
from core.auth import sign_out, is_admin
from utils.helpers import inject_global_css


SIDEBAR_CSS = """
<style>
/* ── Sidebar shell ────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0D1526 !important;
    border-right: 1px solid #1E293B !important;
    min-width: 220px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* Hide the Streamlit collapse arrow on auth-less sidebar */
[data-testid="collapsedControl"] { display: none !important; }

/* ── Suppress Streamlit default page nav list ─────── */
[data-testid="stSidebarNavItems"]  { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── Sidebar buttons ──────────────────────────────── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #64748B !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 7px 12px !important;
    width: 100% !important;
    transition: background 0.15s, color 0.15s !important;
    letter-spacing: 0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1E293B !important;
    color: #F1F5F9 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Sign out button distinct style */
[data-testid="stSidebar"] .stButton[data-testid*="signout"] > button,
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    color: #475569 !important;
}

/* ── Section labels ───────────────────────────────── */
.sb-label {
    font-size: 0.62rem;
    font-weight: 700;
    color: #1E293B;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 0 12px;
    margin: 12px 0 4px;
}

/* ── Divider ──────────────────────────────────────── */
.sb-divider {
    border: none;
    border-top: 1px solid #1E293B;
    margin: 8px 0;
}

/* ── Version tag ──────────────────────────────────── */
.sb-version {
    font-size: 0.6rem;
    color: #1E293B;
    text-align: center;
    padding: 6px;
}
</style>
"""


def render_sidebar():
    """Render the main navigation sidebar on authenticated pages."""
    inject_global_css()
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:18px 14px 10px; border-bottom:1px solid #1E293B; margin-bottom:8px;">
            <div style="font-size:1.25rem; font-weight:800; color:#14B8A6; letter-spacing:-0.02em;">
                The<span style="color:#F59E0B;">Sourcer</span>
            </div>
            <div style="font-size:0.6rem; color:#1E293B; letter-spacing:0.12em;
                        text-transform:uppercase; margin-top:2px;">
                AI Talent Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── User pill ───────────────────────────────────────────────────────
        profile = st.session_state.get("profile") or {}
        name    = (profile.get("full_name") or "Recruiter").strip() or "Recruiter"
        company = profile.get("company") or (profile.get("role") or "user").title()
        initials = name[0].upper()

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:9px;
                    padding:10px 12px; margin:0 0 6px; border-radius:8px;
                    background:#111827;">
            <div style="width:30px; height:30px; border-radius:50%; flex-shrink:0;
                        background:linear-gradient(135deg,#0D9488,#F59E0B);
                        display:flex; align-items:center; justify-content:center;
                        font-weight:800; color:white; font-size:12px;">
                {initials}
            </div>
            <div style="min-width:0; overflow:hidden;">
                <div style="font-size:0.8rem; font-weight:600; color:#E2E8F0;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {name}
                </div>
                <div style="font-size:0.65rem; color:#334155;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {company}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── MAIN section ────────────────────────────────────────────────────
        _label("MAIN")
        _btn("🏠  Dashboard",           "pages/03_Dashboard.py",          "nb_dash")
        _btn("🔍  New Search",           "pages/04_New_Search.py",         "nb_new")
        _btn("👥  Candidate Database",   "pages/06_Candidate_Database.py", "nb_db")
        _btn("🗂️  Saved Searches",      "pages/07_Saved_Searches.py",     "nb_saved")

        _divider()

        # ── TOOLS section ────────────────────────────────────────────────────
        _label("TOOLS")
        _btn("🔤  Boolean Builder",      "pages/11_Boolean_Builder.py",    "nb_bool")
        _btn("✉️  Outreach",             "pages/08_Outreach.py",           "nb_out")

        _divider()

        # ── ACCOUNT section ──────────────────────────────────────────────────
        _label("ACCOUNT")
        _btn("⚙️  Settings",             "pages/09_Settings.py",           "nb_set")
        if is_admin():
            _btn("🛡️  Admin Panel",      "pages/10_Admin.py",              "nb_admin")

        _divider()

        # Sign out
        if st.button("↩  Sign Out", use_container_width=True, key="nb_out_btn"):
            sign_out()

        st.markdown('<div class="sb-version">The Sourcer · v1.0 MVP</div>',
                    unsafe_allow_html=True)


def _btn(label: str, page: str, key: str):
    if st.button(label, use_container_width=True, key=key):
        st.switch_page(page)


def _label(text: str):
    st.markdown(f'<div class="sb-label">{text}</div>', unsafe_allow_html=True)


def _divider():
    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)
