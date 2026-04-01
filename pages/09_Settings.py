import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/09_Settings.py — Settings & Profile
"""
import streamlit as st
from core.auth import require_auth, load_user_session
from core.database import (save_api_keys, get_api_keys, update_profile,
                            get_profile, create_team, get_team)
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css

st.set_page_config(page_title="Settings — The Sourcer", page_icon="⚙️", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">⚙️ Settings</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Manage your API keys, profile, and team settings.
    </div>
</div>
""", unsafe_allow_html=True)

profile = st.session_state.get("profile", {}) or {}
api_keys = get_api_keys(user.id) or {}

tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "👤 Profile", "🤝 Team"])

# ── API KEYS TAB ──────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:20px; margin-bottom:1.5rem;">
        <div style="font-weight:700; color:#F1F5F9; margin-bottom:8px;">🔑 Your API Keys</div>
        <div style="color:#64748B; font-size:0.85rem; line-height:1.6;">
            All keys are stored securely in your account and never shared. They are used exclusively
            to power your searches and AI analysis. You retain full control.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("api_keys_form"):
        st.markdown("#### 🤖 AI Engine (Required for JD Analysis)")
        st.markdown('<div style="color:#64748B; font-size:0.8rem; margin-bottom:8px;">Powers JD analysis, skill matrix, search parameters, outreach generation, and candidate scoring. You can use either Groq (faster) or Anthropic.</div>', unsafe_allow_html=True)
        
        from config import GROQ_API_KEY
        if GROQ_API_KEY:
            st.success("✅ **Groq API Key** is set in system secrets.")
        else:
            st.info("💡 **Groq API Key** not found in system secrets. Using Anthropic if provided.")

        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=api_keys.get("anthropic_key", "") or "",
            type="password",
            placeholder="sk-ant-...",
            help="Get from: console.anthropic.com → API Keys"
        )

        st.markdown("---")
        st.markdown("#### 🔍 Google Custom Search (Required for X-Ray Sourcing)")
        st.markdown('<div style="color:#64748B; font-size:0.8rem; margin-bottom:8px;">Powers LinkedIn X-Ray, job board searches, and web CV discovery. Free: 100 queries/day.</div>', unsafe_allow_html=True)

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            google_api_key = st.text_input(
                "Google API Key",
                value=api_keys.get("google_api_key", "") or "",
                type="password",
                placeholder="AIza...",
                help="Get from: console.developers.google.com → APIs & Services → Credentials"
            )
        with g_col2:
            google_cse_id = st.text_input(
                "Custom Search Engine ID (cx)",
                value=api_keys.get("google_cse_id", "") or "",
                type="password",
                placeholder="a1b2c3d4e...",
                help="Get from: programmablesearchengine.google.com → Create → Copy Search Engine ID"
            )

        st.markdown("---")
        st.markdown("#### 🐙 GitHub Token (Optional — Increases Rate Limits)")
        st.markdown('<div style="color:#64748B; font-size:0.8rem; margin-bottom:8px;">Without token: 10 requests/min. With token: 30 requests/min and more results.</div>', unsafe_allow_html=True)
        github_token = st.text_input(
            "GitHub Personal Access Token",
            value=api_keys.get("github_token", "") or "",
            type="password",
            placeholder="ghp_...",
            help="Get from: github.com → Settings → Developer settings → Personal access tokens → Classic"
        )

        st.markdown("---")
        save_keys_btn = st.form_submit_button("💾 Save API Keys", type="primary", use_container_width=True)

        if save_keys_btn:
            saved = save_api_keys(user.id, {
                "anthropic_key": anthropic_key.strip() or None,
                "google_api_key": google_api_key.strip() or None,
                "google_cse_id": google_cse_id.strip() or None,
                "github_token": github_token.strip() or None,
            })
            if saved:
                st.session_state.api_keys = get_api_keys(user.id)
                st.success("✅ API keys saved successfully!")
            else:
                st.error("Failed to save keys. Please try again.")

    # Setup guides
    with st.expander("📖 How to Get API Keys — Step by Step", expanded=False):
        st.markdown("""
**1. Anthropic API Key (Required)**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up / log in
3. Click **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy and paste it above

---

**2. Google Custom Search API (Required for X-Ray)**

*Step A — Get Google API Key:*
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **API Key**
5. Copy your API Key

*Step B — Enable Custom Search API:*
1. Still in Google Cloud Console
2. Go to **APIs & Services** → **Library**
3. Search for **"Custom Search API"**
4. Click **Enable**

*Step C — Create a Search Engine:*
1. Go to [programmablesearchengine.google.com](https://programmablesearchengine.google.com)
2. Click **Add** → Name it "The Sourcer"
3. Under "Search the entire web", select that option
4. Click **Create**
5. Copy the **Search Engine ID** (cx value)

*Free tier:* 100 searches/day. Upgrade to paid for more.

---

**3. GitHub Token (Optional)**
1. Go to github.com → **Settings** → **Developer settings**
2. Click **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Select scopes: just `read:user` and `user:email`
5. Copy and paste above
""")

    # Key status indicators
    st.markdown("---")
    st.markdown("#### 🔑 Key Status")
    keys = st.session_state.get("api_keys", {}) or {}
    k1, k2, k3 = st.columns(3)
    with k1:
        has_ant = bool(keys.get("anthropic_key"))
        st.markdown(f"{'✅' if has_ant else '❌'} **Anthropic**")
        st.markdown(f'<span style="color:{"#10B981" if has_ant else "#F87171"}; font-size:0.78rem;">{"Connected" if has_ant else "Not configured"}</span>', unsafe_allow_html=True)
    with k2:
        has_goog = bool(keys.get("google_api_key") and keys.get("google_cse_id"))
        st.markdown(f"{'✅' if has_goog else '❌'} **Google CSE**")
        st.markdown(f'<span style="color:{"#10B981" if has_goog else "#F87171"}; font-size:0.78rem;">{"Connected" if has_goog else "Not configured"}</span>', unsafe_allow_html=True)
    with k3:
        has_gh = bool(keys.get("github_token"))
        st.markdown(f"{'✅' if has_gh else '⚪'} **GitHub**")
        st.markdown(f'<span style="color:{"#10B981" if has_gh else "#94A3B8"}; font-size:0.78rem;">{"Connected" if has_gh else "Optional — not set"}</span>', unsafe_allow_html=True)

# ── PROFILE TAB ───────────────────────────────────────────────────────────────
with tab2:
    with st.form("profile_form"):
        st.markdown("#### 👤 Your Profile")

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            full_name = st.text_input("Full Name", value=profile.get("full_name", "") or "")
            company = st.text_input("Company / Organisation", value=profile.get("company", "") or "")
        with p_col2:
            job_title = st.text_input("Your Job Title", value=profile.get("job_title", "") or "",
                                       placeholder="e.g. Senior Recruiter, Talent Partner...")
            email_display = st.text_input("Email", value=profile.get("email", "") or user.email or "",
                                           disabled=True, help="Email cannot be changed here")

        save_profile_btn = st.form_submit_button("💾 Save Profile", type="primary")

        if save_profile_btn:
            updated = update_profile(user.id, {
                "full_name": full_name.strip(),
                "company": company.strip(),
                "job_title": job_title.strip(),
            })
            if updated:
                st.session_state.profile = get_profile(user.id)
                st.success("✅ Profile updated!")
            else:
                st.error("Failed to update profile.")

    # Account info
    st.markdown("---")
    st.markdown("#### 🔐 Account")
    role = profile.get("role", "user")
    created = profile.get("created_at", "")[:10] if profile.get("created_at") else "—"
    st.markdown(f"""
    <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:16px 20px;">
        <div style="display:flex; gap:32px; flex-wrap:wrap;">
            <div>
                <div style="font-size:0.75rem; color:#475569; text-transform:uppercase; letter-spacing:0.05em;">Account Role</div>
                <div style="font-weight:600; color:#F1F5F9; margin-top:4px; text-transform:capitalize;">{role}</div>
            </div>
            <div>
                <div style="font-size:0.75rem; color:#475569; text-transform:uppercase; letter-spacing:0.05em;">Member Since</div>
                <div style="font-weight:600; color:#F1F5F9; margin-top:4px;">{created}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── TEAM TAB ──────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### 🤝 Team Workspace")
    st.markdown('<div style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Share candidates with your team. Team members can view shared candidates in the Candidate Database.</div>', unsafe_allow_html=True)

    team_id = profile.get("team_id")

    if team_id:
        team = get_team(team_id)
        if team:
            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #0D9488; border-radius:10px; padding:16px 20px; margin-bottom:1rem;">
                <div style="font-weight:700; color:#F1F5F9;">🏢 {team.get('name','Team')}</div>
                <div style="color:#64748B; font-size:0.8rem; margin-top:4px;">
                    {len(team.get('team_members',[]))} member(s)
                </div>
            </div>
            """, unsafe_allow_html=True)

            members = team.get("team_members", [])
            for m in members:
                p = m.get("profiles") or {}
                member_name = p.get("full_name", "Unknown") if isinstance(p, dict) else "Unknown"
                member_email = p.get("email", "") if isinstance(p, dict) else ""
                m_role = m.get("role", "member")
                st.markdown(f"- **{member_name}** ({member_email}) — `{m_role}`")
        else:
            st.warning("Team not found.")
    else:
        st.markdown("You are not part of a team yet.")
        with st.form("create_team_form"):
            team_name = st.text_input("Team Name", placeholder="e.g. Talent Acquisition Team")
            create_team_btn = st.form_submit_button("🤝 Create Team", type="primary")
            if create_team_btn and team_name.strip():
                tid = create_team(team_name.strip(), user.id)
                if tid:
                    st.success(f"✅ Team '{team_name}' created!")
                    st.session_state.profile = get_profile(user.id)
                    st.rerun()
