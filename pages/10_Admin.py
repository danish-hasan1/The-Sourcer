import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/10_Admin.py — Admin Panel
"""
import streamlit as st
from core.auth import require_auth, load_user_session, is_admin
from core.database import get_all_profiles_admin, update_profile, get_searches, get_candidates
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state
import pandas as pd

st.set_page_config(page_title="Admin — The Sourcer", page_icon="🛡️", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)

if not is_admin():
    st.error("⛔ Access denied. Admin only.")
    st.stop()

render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">🛡️ Admin Panel</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Manage users, monitor platform usage, and configure system settings.
    </div>
</div>
""", unsafe_allow_html=True)

profiles = get_all_profiles_admin()

# ── Platform stats ─────────────────────────────────────────────────────────────
total_users = len(profiles)
admin_count = sum(1 for p in profiles if p.get("role") == "admin")
user_count = total_users - admin_count

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Users", total_users)
with m2:
    st.metric("Active Recruiters", user_count)
with m3:
    st.metric("Admins", admin_count)
with m4:
    recent = sum(1 for p in profiles if p.get("created_at", "")[:7] == pd.Timestamp.now().strftime("%Y-%m"))
    st.metric("New This Month", recent)

st.markdown("---")

tab1, tab2 = st.tabs(["👥 User Management", "📊 Usage Analytics"])

# ── USER MANAGEMENT ───────────────────────────────────────────────────────────
with tab1:
    q = st.text_input("🔎 Search users", placeholder="Filter by name or email...", label_visibility="collapsed")
    filtered = [p for p in profiles if not q or
                q.lower() in (p.get("full_name") or "").lower() or
                q.lower() in (p.get("email") or "").lower()]

    st.markdown(f'<div style="color:#64748B; font-size:0.8rem; margin-bottom:1rem;">{len(filtered)} users</div>', unsafe_allow_html=True)

    for p in filtered:
        uid = p.get("id")
        name = p.get("full_name") or "—"
        email = p.get("email") or "—"
        role = p.get("role", "user")
        company = p.get("company") or "—"
        created = p.get("created_at", "")[:10] if p.get("created_at") else "—"
        onboarded = "✅" if p.get("onboarding_completed") else "⏳"

        role_colors = {"admin": "#F59E0B", "user": "#14B8A6"}
        rc = role_colors.get(role, "#94A3B8")

        with st.expander(f"{'🛡️' if role == 'admin' else '👤'} {name} — {email}", expanded=False):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"""
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.85rem;">
                    <div>
                        <div style="color:#475569; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em;">Role</div>
                        <div style="color:{rc}; font-weight:600; text-transform:capitalize;">{role}</div>
                    </div>
                    <div>
                        <div style="color:#475569; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em;">Company</div>
                        <div style="color:#F1F5F9;">{company}</div>
                    </div>
                    <div>
                        <div style="color:#475569; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em;">Joined</div>
                        <div style="color:#F1F5F9;">{created}</div>
                    </div>
                    <div>
                        <div style="color:#475569; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em;">Onboarding</div>
                        <div style="color:#F1F5F9;">{onboarded}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_actions:
                # Toggle role
                if uid != user.id:  # Can't change own role
                    new_role = "user" if role == "admin" else "admin"
                    btn_label = "🛡️ Make Admin" if role == "user" else "👤 Remove Admin"
                    if st.button(btn_label, key=f"role_{uid}", use_container_width=True):
                        update_profile(uid, {"role": new_role})
                        st.rerun()
                else:
                    st.markdown('<div style="color:#475569; font-size:0.78rem; text-align:center;">Your account</div>', unsafe_allow_html=True)

    # Export users
    if profiles:
        st.markdown("---")
        df = pd.DataFrame([{
            "Name": p.get("full_name", ""),
            "Email": p.get("email", ""),
            "Role": p.get("role", "user"),
            "Company": p.get("company", ""),
            "Joined": p.get("created_at", "")[:10],
            "Onboarding": "Complete" if p.get("onboarding_completed") else "Pending",
        } for p in profiles])
        st.download_button(
            "📥 Export User List",
            df.to_csv(index=False),
            file_name="users_export.csv",
            mime="text/csv",
        )

# ── USAGE ANALYTICS ───────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### 📊 Platform Activity")
    st.markdown('<div style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Platform-wide usage summary. Individual user data remains private.</div>', unsafe_allow_html=True)

    # Onboarding completion rate
    completed_onboarding = sum(1 for p in profiles if p.get("onboarding_completed"))
    onboarding_rate = int(completed_onboarding / total_users * 100) if total_users else 0

    a1, a2, a3 = st.columns(3)
    with a1:
        st.metric("Onboarding Completion", f"{onboarding_rate}%",
                  help="Users who completed the tutorial")
    with a2:
        teams = len(set(p.get("team_id") for p in profiles if p.get("team_id")))
        st.metric("Active Teams", teams)
    with a3:
        users_this_week = sum(1 for p in profiles
                              if p.get("created_at", "")[:10] >= (pd.Timestamp.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d"))
        st.metric("New Users (7 days)", users_this_week)

    # User role breakdown
    st.markdown("---")
    st.markdown("**User Role Distribution**")
    roles_data = pd.DataFrame({
        "Role": ["Recruiters", "Admins"],
        "Count": [user_count, admin_count],
    })
    st.bar_chart(roles_data.set_index("Role"))

    # Onboarding funnel
    st.markdown("**Onboarding Status**")
    onboard_data = pd.DataFrame({
        "Status": ["Completed", "Pending"],
        "Count": [completed_onboarding, total_users - completed_onboarding],
    })
    st.bar_chart(onboard_data.set_index("Status"))

    # System info
    st.markdown("---")
    st.markdown("**🛠️ System Information**")
    st.markdown(f"""
    <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:16px 20px; font-size:0.82rem; color:#94A3B8; font-family: 'DM Mono', monospace;">
        Platform: The Sourcer MVP v1.0<br>
        AI Model: claude-opus-4-5<br>
        Search: Google Custom Search API + GitHub API + Stack Exchange API<br>
        Database: Supabase (PostgreSQL)<br>
        Deployment: Streamlit Cloud<br>
        Total Registered Users: {total_users}
    </div>
    """, unsafe_allow_html=True)
