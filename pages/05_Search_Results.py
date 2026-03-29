import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/05_Search_Results.py — Search Results
"""
import streamlit as st
from core.auth import require_auth, load_user_session, get_anthropic_key
from core.database import save_candidate, get_candidates
from core.ai_engine import refine_search
from core.sourcing_engine import run_sourcing, get_source_options, get_all_regions
from components.sidebar import render_sidebar
from components.candidate_card import render_candidate_card
from utils.helpers import inject_global_css, empty_state

st.set_page_config(page_title="Search Results — The Sourcer", page_icon="🔍", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">📋 Search Results</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Review, score, save, and reach out to candidates found across all sources.
    </div>
</div>
""", unsafe_allow_html=True)

candidates = st.session_state.get("sourcing_results", [])
filters = st.session_state.get("search_filters", {})
search_id = st.session_state.get("search_id")
anthropic_key = get_anthropic_key()

if not candidates:
    empty_state("🔍", "No results to show", "Run a search from New Search to see candidates here.")
    if st.button("🔍 Go to New Search", type="primary"):
        st.switch_page("pages/04_New_Search.py")
    st.stop()

# ── Summary bar ────────────────────────────────────────────────────────────────
total = len(candidates)
by_source = {}
for c in candidates:
    src = c.get("source_group") or c.get("source") or "Other"
    by_source[src] = by_source.get(src, 0) + 1

source_chips = " ".join([
    f'<span style="background:#1E293B; border:1px solid #334155; border-radius:8px; padding:4px 12px; font-size:11px; color:#94A3B8; margin-right:6px;">'
    f'{k}: <b style="color:#14B8A6">{v}</b></span>'
    for k, v in by_source.items()
])
avg_score = int(sum(c.get("match_score", 0) for c in candidates) / total) if total else 0

st.markdown(f"""
<div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:16px 20px; margin-bottom:1.5rem;
            display:flex; gap:24px; align-items:center; flex-wrap:wrap;">
    <div>
        <span style="font-size:1.4rem; font-weight:800; color:#14B8A6;">{total}</span>
        <span style="color:#64748B; font-size:0.85rem; margin-left:6px;">candidates found</span>
    </div>
    <div>
        <span style="font-size:1.4rem; font-weight:800; color:#F59E0B;">{avg_score}%</span>
        <span style="color:#64748B; font-size:0.85rem; margin-left:6px;">avg match score</span>
    </div>
    <div style="flex:1">{source_chips}</div>
</div>
""", unsafe_allow_html=True)

# ── Controls ───────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 2])
with ctrl1:
    sort_by = st.selectbox("Sort by", ["Match Score ↓", "Match Score ↑", "Name A-Z", "Source"], label_visibility="collapsed")
with ctrl2:
    source_filter = st.multiselect("Filter source", options=list(by_source.keys()),
                                    default=list(by_source.keys()), label_visibility="collapsed")
with ctrl3:
    min_score = st.slider("Min score", 0, 100, 0, 5, label_visibility="collapsed")
with ctrl4:
    save_all_btn = st.button("💾 Save All to Database", use_container_width=True)

# ── Apply filters/sorting ──────────────────────────────────────────────────────
filtered = [c for c in candidates
            if (c.get("source_group") or c.get("source") or "Other") in source_filter
            and c.get("match_score", 0) >= min_score]

sort_map = {
    "Match Score ↓": lambda x: -x.get("match_score", 0),
    "Match Score ↑": lambda x: x.get("match_score", 0),
    "Name A-Z": lambda x: (x.get("full_name") or "").lower(),
    "Source": lambda x: x.get("source", ""),
}
filtered.sort(key=sort_map.get(sort_by, sort_map["Match Score ↓"]))

if save_all_btn:
    saved_count = 0
    for c in filtered:
        save_candidate(user.id, c, search_id=search_id)
        saved_count += 1
    st.success(f"✅ {saved_count} candidates saved to your database!")

# ── Source tabs ────────────────────────────────────────────────────────────────
all_groups = ["All"] + list(by_source.keys())
tabs = st.tabs(all_groups)

saved_ids = set()

for tab_idx, tab in enumerate(tabs):
    with tab:
        group_name = all_groups[tab_idx]
        if group_name == "All":
            show = filtered
        else:
            show = [c for c in filtered if (c.get("source_group") or c.get("source") or "Other") == group_name]

        if not show:
            empty_state("🔍", f"No {group_name} results", "Try broadening your filters.")
            continue

        st.markdown(f'<div style="color:#64748B; font-size:0.8rem; margin-bottom:1rem;">{len(show)} candidates shown</div>', unsafe_allow_html=True)

        for i, candidate in enumerate(show):
            uid = candidate.get("profile_url", str(i))

            def on_save(c, uid=uid):
                if uid not in saved_ids:
                    save_candidate(user.id, c, search_id=search_id)
                    saved_ids.add(uid)
                    st.toast(f"✅ {c.get('full_name', 'Candidate')} saved!", icon="💾")

            def on_outreach(c):
                st.session_state["outreach_candidate"] = c
                jda = (st.session_state.get("ai_results") or {}).get("jd_analysis", {})
                st.session_state["outreach_jd_summary"] = jda.get("ideal_candidate_brief", "")
                st.switch_page("pages/08_Outreach.py")

            render_candidate_card(
                candidate,
                idx=f"{tab_idx}_{i}",
                show_save_button=True,
                show_stage=False,
                on_save=on_save,
                on_outreach=on_outreach,
            )

st.markdown("---")

# ── Rethink Search ─────────────────────────────────────────────────────────────
st.markdown("### 🤔 Not Finding the Right Candidates?")
st.markdown('<div style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Tell the AI what\'s wrong and it will refine the search for you.</div>', unsafe_allow_html=True)

with st.expander("💬 Refine with AI", expanded=False):
    feedback = st.text_area(
        "What's not working?",
        placeholder='e.g. "The candidates are too junior", "I need more fintech experience", "Too many agency recruiters showing up", "Show me candidates from startups only"...',
        height=100,
    )
    refine_btn = st.button("🔄 Rethink Search", type="primary", disabled=not feedback.strip() or not anthropic_key)

    if refine_btn and feedback.strip() and anthropic_key:
        with st.spinner("🧠 AI is refining your search..."):
            refined = refine_search(
                api_key=anthropic_key,
                current_filters=filters,
                user_feedback=feedback,
                results_so_far=total,
            )

        if refined:
            st.markdown("**✅ Suggested refinements:**")
            if refined.get("reasoning"):
                st.info(refined["reasoning"])

            apply_col1, apply_col2 = st.columns(2)
            with apply_col1:
                if refined.get("updated_titles"):
                    st.markdown("**Updated Titles:**")
                    for t in refined["updated_titles"]:
                        st.markdown(f"- {t}")
                if refined.get("updated_boolean"):
                    st.markdown(f"**New Boolean:** `{refined['updated_boolean']}`")

            with apply_col2:
                if refined.get("updated_skills"):
                    st.markdown("**Updated Skills:**")
                    for s in refined["updated_skills"]:
                        st.markdown(f"- {s}")
                if refined.get("additional_sources"):
                    st.markdown("**Also try:**")
                    for src in refined["additional_sources"]:
                        st.markdown(f"- {src}")

            if st.button("✅ Apply These Changes & Re-Search", type="primary"):
                # Update filters and go back to search
                current = st.session_state.search_filters.copy()
                if refined.get("updated_titles"):
                    current["job_titles"] = refined["updated_titles"]
                if refined.get("updated_skills"):
                    current["skills"] = refined["updated_skills"]
                if refined.get("updated_boolean"):
                    current["boolean_string"] = refined["updated_boolean"]
                if refined.get("updated_location"):
                    current["location"] = refined["updated_location"]
                st.session_state.search_filters = current
                st.session_state.sourcing_results = None
                st.switch_page("pages/04_New_Search.py")

# ── Back to search ─────────────────────────────────────────────────────────────
col_back1, col_back2 = st.columns([1, 4])
with col_back1:
    if st.button("← New Search"):
        st.switch_page("pages/04_New_Search.py")
