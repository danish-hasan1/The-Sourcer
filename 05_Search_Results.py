import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/05_Search_Results.py — Search Results
Full rebuild: better UX, bulk save, sticky filters, refine flow.
"""
import streamlit as st
from core.auth import require_auth, load_user_session, get_anthropic_key
from core.database import save_candidate, get_candidates
from core.ai_engine import refine_search
from components.sidebar import render_sidebar
from components.candidate_card import render_candidate_card
from utils.helpers import inject_global_css, empty_state

st.set_page_config(
    page_title="Search Results — The Sourcer",
    page_icon="📋",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.25rem 0 0.75rem;">
    <div style="font-size:1.5rem; font-weight:800; color:#F1F5F9;">📋 Search Results</div>
    <div style="color:#64748B; font-size:0.85rem; margin-top:3px;">
        Review, score, save and reach out to candidates found across all sources.
    </div>
</div>
""", unsafe_allow_html=True)

candidates = st.session_state.get("sourcing_results", [])
filters    = st.session_state.get("search_filters", {})
search_id  = st.session_state.get("search_id")
anthropic_key = get_anthropic_key()

# ── Empty state ────────────────────────────────────────────────────────────────
if not candidates:
    empty_state(
        "🔍",
        "No results to show",
        "Run a search from New Search to see candidates here.",
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 New Search", type="primary", use_container_width=True):
            st.switch_page("pages/04_New_Search.py")
    st.stop()

# ── Compute source breakdown ───────────────────────────────────────────────────
total    = len(candidates)
by_source = {}
for c in candidates:
    src = c.get("source_group") or c.get("source") or "Other"
    by_source[src] = by_source.get(src, 0) + 1

scored    = [c for c in candidates if c.get("match_score", 0) > 0]
avg_score = int(sum(c["match_score"] for c in scored) / len(scored)) if scored else 0

# ── Summary banner ─────────────────────────────────────────────────────────────
src_chips = "".join(
    f'<span style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; '
    f'padding:3px 10px; font-size:11px; color:#64748B; margin-right:4px;">'
    f'{k} <b style="color:#14B8A6">{v}</b></span>'
    for k, v in by_source.items()
)
st.markdown(f"""
<div style="background:#1E293B; border:1px solid #334155; border-radius:12px;
            padding:14px 20px; margin-bottom:1.25rem;
            display:flex; align-items:center; gap:28px; flex-wrap:wrap;">
    <div>
        <span style="font-size:1.5rem; font-weight:800; color:#14B8A6;">{total}</span>
        <span style="color:#475569; font-size:0.82rem; margin-left:6px;">candidates found</span>
    </div>
    <div>
        <span style="font-size:1.5rem; font-weight:800; color:#F59E0B;">{avg_score}%</span>
        <span style="color:#475569; font-size:0.82rem; margin-left:6px;">avg match</span>
    </div>
    <div style="flex:1; min-width:0;">{src_chips}</div>
    <div style="font-size:0.75rem; color:#334155; flex-shrink:0;">
        {'🎯 AI scored' if scored else '⚡ No AI scoring — add Anthropic key in Settings'}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Controls bar ───────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([2, 2, 1.5, 1.5, 1.5])
with ctrl1:
    sort_by = st.selectbox(
        "Sort",
        ["Match Score ↓", "Match Score ↑", "Name A–Z", "Source"],
        label_visibility="collapsed",
    )
with ctrl2:
    src_opts    = list(by_source.keys())
    src_filter  = st.multiselect(
        "Source filter",
        options=src_opts,
        default=src_opts,
        label_visibility="collapsed",
        placeholder="All sources",
    )
with ctrl3:
    min_score = st.number_input(
        "Min score", min_value=0, max_value=100, value=0, step=5,
        label_visibility="collapsed",
    )
with ctrl4:
    name_q = st.text_input(
        "Search name/skill",
        placeholder="Filter by name…",
        label_visibility="collapsed",
    )
with ctrl5:
    if st.button("💾 Save All", use_container_width=True, type="primary"):
        st.session_state["_save_all"] = True

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = candidates
if src_filter:
    filtered = [c for c in filtered
                if (c.get("source_group") or c.get("source") or "Other") in src_filter]
if min_score:
    filtered = [c for c in filtered if c.get("match_score", 0) >= min_score]
if name_q:
    q = name_q.lower()
    filtered = [c for c in filtered
                if q in (c.get("full_name") or "").lower()
                or any(q in s.lower() for s in (c.get("skills") or []))]

sort_fns = {
    "Match Score ↓": lambda x: -(x.get("match_score") or 0),
    "Match Score ↑": lambda x:  (x.get("match_score") or 0),
    "Name A–Z":      lambda x:  (x.get("full_name") or "").lower(),
    "Source":        lambda x:  (x.get("source") or ""),
}
filtered.sort(key=sort_fns.get(sort_by, sort_fns["Match Score ↓"]))

st.markdown(
    f'<div style="color:#475569; font-size:0.78rem; margin-bottom:0.75rem;">'
    f'Showing {len(filtered)} of {total} candidates</div>',
    unsafe_allow_html=True,
)

# ── Save all handler ───────────────────────────────────────────────────────────
if st.session_state.pop("_save_all", False):
    saved_n = 0
    already = {c.get("profile_url") for c in get_candidates(user.id, search_id=search_id)}
    for c in filtered:
        if c.get("profile_url") not in already:
            save_candidate(user.id, c, search_id=search_id)
            saved_n += 1
    st.success(f"✅ {saved_n} new candidates saved to your database!")
    st.rerun()

# ── Source tabs ────────────────────────────────────────────────────────────────
tab_labels = ["All"] + list(by_source.keys())
tabs       = st.tabs(tab_labels)

_saved_urls = set()  # track what was saved this session

for t_idx, tab in enumerate(tabs):
    with tab:
        group = tab_labels[t_idx]
        show  = filtered if group == "All" else [
            c for c in filtered
            if (c.get("source_group") or c.get("source") or "Other") == group
        ]

        if not show:
            empty_state("🔍", f"No {group} results match your filters.")
            continue

        st.markdown(
            f'<div style="color:#475569; font-size:0.78rem; '
            f'margin:6px 0 10px;">{len(show)} candidates</div>',
            unsafe_allow_html=True,
        )

        for i, candidate in enumerate(show):
            uid = candidate.get("profile_url") or f"{t_idx}_{i}"

            def _on_save(c, _uid=uid):
                if _uid not in _saved_urls:
                    save_candidate(user.id, c, search_id=search_id)
                    _saved_urls.add(_uid)
                    st.toast(
                        f"💾 {c.get('full_name','Candidate')} saved!",
                        icon="✅",
                    )

            def _on_outreach(c):
                st.session_state["outreach_candidate"] = c
                jda = (st.session_state.get("ai_results") or {}).get("jd_analysis", {})
                st.session_state["outreach_jd_summary"] = (
                    jda.get("ideal_candidate_brief", "")
                )
                st.switch_page("pages/08_Outreach.py")

            render_candidate_card(
                candidate,
                idx=f"{t_idx}_{i}",
                show_save_button=True,
                show_stage=False,
                on_save=_on_save,
                on_outreach=_on_outreach,
            )

# ── Rethink Search ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:20px 22px; margin-top:0.5rem;">
    <div style="font-size:1rem; font-weight:700; color:#F1F5F9; margin-bottom:4px;">
        🤔 Not finding the right candidates?
    </div>
    <div style="color:#64748B; font-size:0.83rem;">
        Tell the AI what's wrong and it will refine the search parameters for you.
    </div>
</div>
""", unsafe_allow_html=True)

feedback = st.text_area(
    "What's not working?",
    placeholder=(
        'Examples:\n'
        '"Candidates are too junior"\n'
        '"Need more fintech experience"\n'
        '"Too many agency recruiters appearing"\n'
        '"Show me startup backgrounds only"'
    ),
    height=110,
    label_visibility="collapsed",
)

ref_col1, ref_col2, ref_col3 = st.columns([2, 1, 3])
with ref_col1:
    refine_btn = st.button(
        "🔄 Rethink Search with AI",
        type="primary",
        use_container_width=True,
        disabled=not feedback.strip() or not anthropic_key,
    )
with ref_col2:
    if st.button("← Edit Filters", use_container_width=True):
        st.switch_page("pages/04_New_Search.py")

if refine_btn and feedback.strip():
    if not anthropic_key:
        st.warning("Add your Anthropic API key in Settings to use AI refinement.")
    else:
        with st.spinner("🧠 AI is rethinking your search…"):
            refined = refine_search(
                api_key=anthropic_key,
                current_filters=filters,
                user_feedback=feedback,
                results_so_far=total,
            )

        if refined:
            st.markdown("### ✅ AI Suggestions")

            r1, r2 = st.columns(2)
            with r1:
                if refined.get("reasoning"):
                    st.info(refined["reasoning"])
                if refined.get("updated_titles"):
                    st.markdown("**Updated Titles:**")
                    for t in refined["updated_titles"]:
                        st.markdown(f"- `{t}`")
                if refined.get("updated_boolean"):
                    st.markdown("**New Boolean String:**")
                    st.code(refined["updated_boolean"], language=None)
            with r2:
                if refined.get("updated_skills"):
                    st.markdown("**Updated Skills:**")
                    for s in refined["updated_skills"]:
                        st.markdown(f"- {s}")
                if refined.get("additional_sources"):
                    st.markdown("**Also try sourcing from:**")
                    for src in refined["additional_sources"]:
                        st.markdown(f"- {src}")

            if st.button("✅ Apply Changes & Re-Run Search", type="primary"):
                curr = st.session_state.get("search_filters", {}).copy()
                if refined.get("updated_titles"):
                    curr["job_titles"] = refined["updated_titles"]
                if refined.get("updated_skills"):
                    curr["skills"] = refined["updated_skills"]
                if refined.get("updated_boolean"):
                    curr["boolean_string"] = refined["updated_boolean"]
                if refined.get("updated_location"):
                    curr["location"] = refined["updated_location"]
                st.session_state.search_filters   = curr
                st.session_state.sourcing_results = None
                st.switch_page("pages/04_New_Search.py")
        else:
            st.error("Could not generate refinements. Check your API key.")
