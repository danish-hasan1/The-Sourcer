import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/03_Dashboard.py — Main Dashboard
"""
import streamlit as st
from core.auth import require_auth, load_user_session
from core.database import get_candidate_stats, get_searches, get_jd_library
from components.sidebar import render_sidebar
from components.onboarding import render_onboarding
from utils.helpers import inject_global_css, empty_state
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(page_title="Dashboard — The Sourcer", page_icon="🎯", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

# Show onboarding for first-time users
if render_onboarding():
    st.stop()

profile    = st.session_state.get("profile") or {}
name       = (profile.get("full_name") or "there").split()[0]
api_keys   = st.session_state.get("api_keys") or {}

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">
        Good day, <span style="color:#14B8A6;">{name}</span> 👋
    </div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Here's what's happening across your sourcing pipeline.
    </div>
</div>
""", unsafe_allow_html=True)

# ── API key alert ──────────────────────────────────────────────────────────────
missing_keys = []
if not api_keys.get("anthropic_key"):
    missing_keys.append("Anthropic")
if not api_keys.get("google_api_key") or not api_keys.get("google_cse_id"):
    missing_keys.append("Google Custom Search")

if missing_keys:
    st.warning(
        f"⚠️ **API keys needed:** {', '.join(missing_keys)}. "
        "Add them in **Settings** before running searches.",
        icon="🔑",
    )
    if st.button("⚙️ Go to Settings →"):
        st.switch_page("pages/09_Settings.py")
    st.markdown("---")

# ── Stats ──────────────────────────────────────────────────────────────────────
stats   = get_candidate_stats(user.id)
searches = get_searches(user.id)
jds      = get_jd_library(user.id)

cols = st.columns(6)
metric_data = [
    ("Total Candidates", stats["total"],    "#14B8A6"),
    ("Sourced",          stats["sourced"],   "#7DCFFF"),
    ("Reviewed",         stats["reviewed"],  "#86EFAC"),
    ("Contacted",        stats["contacted"], "#FCD34D"),
    ("Responded",        stats["responded"], "#A5B4FC"),
    ("Interviews",       stats["interview"], "#F0ABFC"),
]
for col, (label, val, color) in zip(cols, metric_data):
    with col:
        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:12px;
                    padding:16px 14px; text-align:center;">
            <div style="font-size:1.8rem; font-weight:800; color:{color};">{val}</div>
            <div style="font-size:0.72rem; color:#475569; text-transform:uppercase;
                        letter-spacing:0.06em; margin-top:4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Main grid ──────────────────────────────────────────────────────────────────
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("### 🔍 Recent Searches")

    if searches:
        for s in searches[:6]:
            jd_meta = s.get("jd_library") or {}
            jd_title = jd_meta.get("title", "—") if isinstance(jd_meta, dict) else "—"
            count  = s.get("result_count", 0)
            status = s.get("status", "completed")
            sdate  = (s.get("created_at") or "")[:10]
            sources = s.get("sources") or []

            status_colors = {
                "completed": "#10B981", "running": "#F59E0B",
                "draft": "#94A3B8",     "paused": "#6366F1",
            }
            sc = status_colors.get(status, "#94A3B8")

            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                        padding:14px 18px; margin-bottom:6px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-weight:600; color:#F1F5F9; font-size:0.95rem;">
                            {s.get("name","Unnamed Search")}
                        </div>
                        <div style="color:#64748B; font-size:0.78rem; margin-top:3px;">
                            📄 {jd_title} · {count} candidates · {sdate}
                        </div>
                        <div style="margin-top:6px; display:flex; gap:4px; flex-wrap:wrap;">
                            {''.join(f'<span style="background:#0F172A;border:1px solid #1E293B;border-radius:5px;padding:1px 7px;font-size:10px;color:#475569;">{src}</span>' for src in sources[:3])}
                        </div>
                    </div>
                    <span style="background:{sc}20; color:{sc}; border-radius:999px;
                                 padding:2px 10px; font-size:11px; font-weight:600;
                                 white-space:nowrap; flex-shrink:0;">
                        {status.title()}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_a, btn_b = st.columns(2)
            with btn_a:
                if st.button("▶ Resume", key=f"res_{s['id']}", use_container_width=True):
                    st.session_state["resume_search"] = s
                    st.switch_page("pages/04_New_Search.py")
            with btn_b:
                if st.button("👥 Candidates", key=f"cands_{s['id']}", use_container_width=True):
                    st.session_state["filter_search_id"] = s["id"]
                    st.switch_page("pages/06_Candidate_Database.py")
    else:
        empty_state("🔍", "No searches yet",
                    "Paste a job description and hit Search to get started.")
        if st.button("🚀 Start First Search", type="primary"):
            st.switch_page("pages/04_New_Search.py")

with right:
    # Pipeline donut
    if stats["total"] > 0:
        st.markdown("### 📊 Pipeline")
        stages = ["Sourced", "Reviewed", "Contacted", "Responded", "Interview"]
        values = [stats["sourced"], stats["reviewed"], stats["contacted"],
                  stats["responded"], stats["interview"]]
        colors = ["#7DCFFF", "#86EFAC", "#FCD34D", "#A5B4FC", "#F0ABFC"]

        non_zero = [(l, v, c) for l, v, c in zip(stages, values, colors) if v > 0]
        if non_zero and HAS_PLOTLY:
            fig = go.Figure(data=[go.Pie(
                labels=[x[0] for x in non_zero],
                values=[x[1] for x in non_zero],
                hole=0.65,
                marker_colors=[x[2] for x in non_zero],
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value} candidates<extra></extra>",
            )])
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="v", x=1.0, font=dict(color="#64748B", size=10)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=0, r=80),
                height=200,
                annotations=[dict(
                    text=f"<b>{stats['total']}</b>",
                    x=0.37, y=0.5,
                    font=dict(size=22, color="#F1F5F9"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        elif non_zero:
            # Fallback if plotly not installed
            for label, val, color in non_zero:
                pct = int(val / stats["total"] * 100) if stats["total"] else 0
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;margin:4px 0;">' +
                    f'<span style="color:{color};font-size:0.82rem;">{label}</span>' +
                    f'<span style="color:#F1F5F9;font-weight:700;">{val}</span></div>',
                    unsafe_allow_html=True
                )
    else:
        st.markdown("### 📊 Pipeline")
        empty_state("📊", "No candidates yet")

    st.markdown("---")

    # JD Library quick panel
    st.markdown("### 📄 JD Library")
    if jds:
        for jd in jds[:5]:
            j1, j2 = st.columns([3, 1])
            with j1:
                st.markdown(f'<div style="color:#F1F5F9;font-size:0.85rem;font-weight:500;'
                            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                            f'{jd.get("title","Untitled")}</div>', unsafe_allow_html=True)
            with j2:
                if st.button("Use", key=f"jd_{jd['id']}", use_container_width=True):
                    st.session_state["prefill_jd"] = jd
                    st.switch_page("pages/04_New_Search.py")
    else:
        st.markdown('<div style="color:#475569;font-size:0.85rem;">No saved JDs yet.</div>',
                    unsafe_allow_html=True)

    if st.button("📄 Full JD Library →", use_container_width=True):
        st.switch_page("pages/07_Saved_Searches.py")

# ── Quick actions ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⚡ Quick Actions")
qa1, qa2, qa3, qa4, qa5 = st.columns(5)
with qa1:
    if st.button("🔍 New Search", use_container_width=True, type="primary"):
        st.switch_page("pages/04_New_Search.py")
with qa2:
    if st.button("👥 Candidates", use_container_width=True):
        st.switch_page("pages/06_Candidate_Database.py")
with qa3:
    if st.button("🔤 Boolean Builder", use_container_width=True):
        st.switch_page("pages/11_Boolean_Builder.py")
with qa4:
    if st.button("✉️ Outreach", use_container_width=True):
        st.switch_page("pages/08_Outreach.py")
with qa5:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/09_Settings.py")
