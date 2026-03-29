import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/06_Candidate_Database.py — Candidate Database & Pipeline
"""
import streamlit as st
import pandas as pd
from core.auth import require_auth, load_user_session
from core.database import get_candidates, update_candidate_stage, update_candidate_notes, delete_candidate, get_searches
from components.sidebar import render_sidebar
from components.candidate_card import render_candidate_card
from utils.helpers import inject_global_css, empty_state, stage_color, source_icon

st.set_page_config(page_title="Candidate Database — The Sourcer", page_icon="👥", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">👥 Candidate Database</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Manage your saved candidates, track pipeline stages, and collaborate with your team.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
filter_search_id = st.session_state.pop("filter_search_id", None)
all_candidates = get_candidates(user.id)
searches = get_searches(user.id)

if not all_candidates:
    empty_state("👥", "No candidates saved yet",
                "Run a search and save candidates to build your database.")
    if st.button("🔍 Start a Search", type="primary"):
        st.switch_page("pages/04_New_Search.py")
    st.stop()

# ── View toggle ────────────────────────────────────────────────────────────────
view_mode = st.radio("View", ["Pipeline View", "List View", "Table View"], horizontal=True, label_visibility="collapsed")

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔽 Filters", expanded=False):
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        stage_filter = st.multiselect("Stage", ["sourced", "reviewed", "contacted", "responded", "interview", "rejected"],
                                       default=["sourced", "reviewed", "contacted", "responded", "interview"])
    with f2:
        source_opts = list(set(c.get("source", "Unknown") for c in all_candidates))
        source_filter = st.multiselect("Source", source_opts, default=source_opts)
    with f3:
        search_opts = {"All searches": None}
        for s in searches:
            search_opts[s.get("name", "Unnamed")] = s.get("id")
        selected_search_label = st.selectbox("Search", list(search_opts.keys()))
        selected_search_id = search_opts[selected_search_label]
        if filter_search_id:
            selected_search_id = filter_search_id
    with f4:
        min_score_db = st.slider("Min Match Score", 0, 100, 0, 5)

    search_name_filter = st.text_input("🔎 Search by name or skill", placeholder="Filter candidates...")

# Apply filters
filtered = all_candidates
if stage_filter:
    filtered = [c for c in filtered if c.get("stage", "sourced") in stage_filter]
if source_filter:
    filtered = [c for c in filtered if c.get("source", "") in source_filter]
if selected_search_id:
    filtered = [c for c in filtered if c.get("search_id") == selected_search_id]
if min_score_db:
    filtered = [c for c in filtered if c.get("match_score", 0) >= min_score_db]
if search_name_filter:
    q = search_name_filter.lower()
    filtered = [c for c in filtered if
                q in (c.get("full_name") or "").lower() or
                any(q in s.lower() for s in (c.get("skills") or []))]

st.markdown(f'<div style="color:#64748B; font-size:0.8rem; margin-bottom:1rem;">{len(filtered)} candidates · {len(all_candidates)} total</div>', unsafe_allow_html=True)

STAGES = ["sourced", "reviewed", "contacted", "responded", "interview", "rejected"]

# ── PIPELINE VIEW ──────────────────────────────────────────────────────────────
if view_mode == "Pipeline View":
    stage_cols = st.columns(len(STAGES))

    for col_idx, stage in enumerate(STAGES):
        with stage_cols[col_idx]:
            stage_candidates = [c for c in filtered if c.get("stage", "sourced") == stage]
            sc = stage_color(stage)
            st.markdown(f"""
            <div style="background:{sc}15; border:1px solid {sc}40; border-radius:10px;
                        padding:10px 12px; margin-bottom:12px; text-align:center;">
                <div style="font-weight:700; color:{sc}; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em;">
                    {stage.title()}
                </div>
                <div style="font-size:1.4rem; font-weight:800; color:#F1F5F9;">{len(stage_candidates)}</div>
            </div>
            """, unsafe_allow_html=True)

            for c in stage_candidates:
                name = c.get("full_name") or "Unknown"
                title = c.get("current_title") or ""
                score = c.get("match_score", 0)
                url = c.get("profile_url", "")
                c_id = c.get("id")
                s_icon = source_icon(c.get("source", ""))

                st.markdown(f"""
                <div style="background:#1E293B; border:1px solid #334155; border-left:3px solid {sc};
                            border-radius:8px; padding:10px 12px; margin-bottom:8px;">
                    <div style="font-weight:600; color:#F1F5F9; font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{name}</div>
                    <div style="color:#64748B; font-size:0.75rem; margin-top:2px;">{s_icon} {title[:35]}{'…' if len(title)>35 else ''}</div>
                    <div style="color:#14B8A6; font-size:0.8rem; font-weight:700; margin-top:4px;">{score}% match</div>
                </div>
                """, unsafe_allow_html=True)

                # Stage move buttons
                mv1, mv2, mv3 = st.columns(3)
                with mv1:
                    if url:
                        st.link_button("🔗", url, use_container_width=True)
                with mv2:
                    # Move forward
                    current_idx = STAGES.index(stage)
                    if current_idx < len(STAGES) - 1:
                        next_stage = STAGES[current_idx + 1]
                        if st.button("→", key=f"fwd_{c_id}", use_container_width=True,
                                     help=f"Move to {next_stage}"):
                            update_candidate_stage(c_id, next_stage)
                            st.rerun()
                with mv3:
                    if st.button("✉️", key=f"out_{c_id}", use_container_width=True, help="Draft outreach"):
                        st.session_state["outreach_candidate"] = c
                        st.switch_page("pages/08_Outreach.py")

# ── LIST VIEW ──────────────────────────────────────────────────────────────────
elif view_mode == "List View":
    export_col, _ = st.columns([1, 4])
    with export_col:
        if filtered:
            export_data = pd.DataFrame([{
                "Name": c.get("full_name", ""),
                "Title": c.get("current_title", ""),
                "Location": c.get("location", ""),
                "Source": c.get("source", ""),
                "Match Score": c.get("match_score", 0),
                "Stage": c.get("stage", ""),
                "Skills": ", ".join(c.get("skills") or []),
                "Profile URL": c.get("profile_url", ""),
            } for c in filtered])
            st.download_button(
                "📥 Export CSV",
                export_data.to_csv(index=False),
                file_name="candidates_export.csv",
                mime="text/csv",
                use_container_width=True,
            )

    for i, candidate in enumerate(filtered):
        c_id = candidate.get("id")
        current_stage = candidate.get("stage", "sourced")

        col_card, col_actions = st.columns([4, 1])
        with col_card:
            render_candidate_card(
                candidate, idx=f"db_{i}",
                show_save_button=False,
                show_stage=True,
            )
        with col_actions:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            new_stage = st.selectbox(
                "Stage",
                STAGES,
                index=STAGES.index(current_stage) if current_stage in STAGES else 0,
                key=f"stage_sel_{c_id}",
                label_visibility="collapsed"
            )
            if new_stage != current_stage:
                update_candidate_stage(c_id, new_stage)
                st.rerun()

            notes = candidate.get("notes") or ""
            new_notes = st.text_area("Notes", value=notes, key=f"notes_{c_id}",
                                      height=80, label_visibility="collapsed",
                                      placeholder="Add notes...")
            if new_notes != notes:
                update_candidate_notes(c_id, new_notes)

            if st.button("🗑️", key=f"del_{c_id}", help="Remove candidate"):
                delete_candidate(c_id)
                st.rerun()

# ── TABLE VIEW ─────────────────────────────────────────────────────────────────
elif view_mode == "Table View":
    df = pd.DataFrame([{
        "Name": c.get("full_name", ""),
        "Title": c.get("current_title", ""),
        "Location": c.get("location", ""),
        "Source": c.get("source", ""),
        "Score": f"{c.get('match_score', 0)}%",
        "Stage": c.get("stage", "sourced").title(),
        "Skills": ", ".join((c.get("skills") or [])[:4]),
        "Profile": c.get("profile_url", ""),
    } for c in filtered])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Profile": st.column_config.LinkColumn("Profile"),
            "Score": st.column_config.TextColumn("Score"),
        }
    )

    if filtered:
        st.download_button(
            "📥 Export CSV",
            df.to_csv(index=False),
            file_name="candidates_export.csv",
            mime="text/csv",
        )
