import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/07_Saved_Searches.py — Saved Searches & JD Library
"""
import streamlit as st
from core.auth import require_auth, load_user_session
from core.database import get_searches, get_jd_library, delete_search, delete_jd
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state

st.set_page_config(page_title="Saved Searches — The Sourcer", page_icon="🗂️", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">🗂️ Saved Searches & JD Library</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Resume past searches, reuse job descriptions, and manage your sourcing history.
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Saved Searches", "📄 JD Library"])

# ── SAVED SEARCHES TAB ────────────────────────────────────────────────────────
with tab1:
    searches = get_searches(user.id)

    if not searches:
        empty_state("🔍", "No saved searches yet",
                    "Run a search and it will be automatically saved here.")
        if st.button("🔍 Start a Search", type="primary"):
            st.switch_page("pages/04_New_Search.py")
    else:
        # Search filter
        q = st.text_input("🔎 Filter searches", placeholder="Search by name...", label_visibility="collapsed")
        filtered = [s for s in searches if not q or q.lower() in (s.get("name") or "").lower()]

        st.markdown(f'<div style="color:#64748B; font-size:0.8rem; margin-bottom:1rem;">{len(filtered)} searches</div>', unsafe_allow_html=True)

        for s in filtered:
            s_id = s.get("id")
            name = s.get("name", "Unnamed Search")
            result_count = s.get("result_count", 0)
            status = s.get("status", "completed")
            created = s.get("created_at", "")[:10] if s.get("created_at") else ""
            jd_info = s.get("jd_library") or {}
            jd_title = jd_info.get("title", "—") if isinstance(jd_info, dict) else "—"
            filters = s.get("filters", {})
            sources = s.get("sources", [])

            status_colors = {
                "completed": ("#10B981", "Completed"),
                "running": ("#F59E0B", "Running"),
                "draft": ("#94A3B8", "Draft"),
                "paused": ("#6366F1", "Paused"),
            }
            sc, sl = status_colors.get(status, ("#94A3B8", status.title()))

            with st.container():
                st.markdown(f"""
                <div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:18px 20px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                        <div style="flex:1;">
                            <div style="font-size:1rem; font-weight:700; color:#F1F5F9;">{name}</div>
                            <div style="color:#64748B; font-size:0.8rem; margin-top:4px;">
                                📄 {jd_title} &nbsp;·&nbsp; {result_count} candidates &nbsp;·&nbsp; {created}
                            </div>
                            <div style="margin-top:8px; display:flex; gap:6px; flex-wrap:wrap;">
                                {''.join(f'<span style="background:#0F172A; border:1px solid #334155; border-radius:6px; padding:2px 8px; font-size:10px; color:#64748B;">{src}</span>' for src in (sources or [])[:4])}
                            </div>
                            {"<div style='margin-top:6px; color:#64748B; font-size:0.78rem;'>📍 " + filters.get('location','') + "</div>" if filters.get('location') else ""}
                        </div>
                        <span style="background:{sc}20; color:{sc}; border-radius:999px; padding:3px 12px; font-size:11px; font-weight:600; white-space:nowrap;">
                            {sl}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn1, btn2, btn3, btn4 = st.columns(4)
                with btn1:
                    if st.button("▶ Resume Search", key=f"res_{s_id}", use_container_width=True, type="primary"):
                        st.session_state["resume_search"] = s
                        st.switch_page("pages/04_New_Search.py")
                with btn2:
                    if st.button("👥 View Candidates", key=f"cands_{s_id}", use_container_width=True):
                        st.session_state["filter_search_id"] = s_id
                        st.switch_page("pages/06_Candidate_Database.py")
                with btn3:
                    # Clone search
                    if st.button("📋 Clone & Edit", key=f"clone_{s_id}", use_container_width=True):
                        st.session_state["resume_search"] = {**s, "name": f"Copy of {name}", "id": None}
                        st.switch_page("pages/04_New_Search.py")
                with btn4:
                    if st.button("🗑️ Delete", key=f"del_{s_id}", use_container_width=True):
                        delete_search(s_id)
                        st.rerun()

                # Show boolean strings on expand
                with st.expander("🔤 View Boolean Strings", expanded=False):
                    bs = s.get("boolean_strings") or {}
                    if bs.get("primary"):
                        st.markdown("**Primary:**")
                        st.code(bs.get("primary", ""), language=None)
                    if bs.get("broad"):
                        st.markdown("**Broad:**")
                        st.code(bs.get("broad", ""), language=None)
                    if bs.get("narrow"):
                        st.markdown("**Narrow:**")
                        st.code(bs.get("narrow", ""), language=None)

                    # Skills & titles
                    f = s.get("filters", {})
                    if f.get("job_titles"):
                        st.markdown(f"**Titles:** {', '.join(f['job_titles'][:5])}")
                    if f.get("skills"):
                        st.markdown(f"**Skills:** {', '.join(f['skills'][:6])}")

# ── JD LIBRARY TAB ────────────────────────────────────────────────────────────
with tab2:
    jds = get_jd_library(user.id)

    if not jds:
        empty_state("📄", "No JDs saved yet",
                    "Check 'Save JD to Library' when running a search.")
    else:
        jd_q = st.text_input("🔎 Filter JDs", placeholder="Search by title...", label_visibility="collapsed", key="jd_q")
        filtered_jds = [j for j in jds if not jd_q or jd_q.lower() in (j.get("title") or "").lower()]

        for jd in filtered_jds:
            jd_id = jd.get("id")
            title = jd.get("title", "Untitled")
            created = jd.get("created_at", "")[:10] if jd.get("created_at") else ""
            jd_text = jd.get("jd_text", "")
            has_analysis = bool(jd.get("ai_analysis"))

            with st.container():
                st.markdown(f"""
                <div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:16px 20px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#F1F5F9; font-size:0.95rem;">{title}</div>
                            <div style="color:#64748B; font-size:0.78rem; margin-top:3px;">
                                Saved {created} &nbsp;·&nbsp;
                                {"✅ AI analysed" if has_analysis else "⏳ Not yet analysed"}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                jd_col1, jd_col2, jd_col3, jd_col4 = st.columns(4)
                with jd_col1:
                    if st.button("🔍 Start Search", key=f"startjd_{jd_id}", use_container_width=True, type="primary"):
                        st.session_state["prefill_jd"] = jd
                        st.switch_page("pages/04_New_Search.py")
                with jd_col2:
                    with st.expander("📄 View JD", expanded=False):
                        st.text_area("", value=jd_text, height=200, key=f"jd_view_{jd_id}",
                                     label_visibility="collapsed", disabled=True)
                with jd_col3:
                    if has_analysis:
                        with st.expander("🧠 View Analysis", expanded=False):
                            analysis = jd.get("ai_analysis", {})
                            seniority = analysis.get("seniority", {})
                            st.markdown(f"**Seniority:** `{seniority.get('level','—').upper()}`")
                            st.markdown(f"**Ideal Candidate:** {analysis.get('ideal_candidate_brief','—')[:300]}")
                            comps = analysis.get("primary_competencies", [])
                            if comps:
                                st.markdown("**Must-Have Skills:**")
                                for c in comps[:5]:
                                    st.markdown(f"- {c.get('name')}")
                with jd_col4:
                    if st.button("🗑️ Delete JD", key=f"deljd_{jd_id}", use_container_width=True):
                        delete_jd(jd_id)
                        st.rerun()
