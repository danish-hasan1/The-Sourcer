import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/06_Candidate_Database.py — Candidate Database & Pipeline
Full rebuild: cleaner pipeline, inline notes, better table view.
"""
import streamlit as st
import pandas as pd
from core.auth import require_auth, load_user_session
from core.database import (
    get_candidates, update_candidate_stage,
    update_candidate_notes, delete_candidate, get_searches,
)
from components.sidebar import render_sidebar
from components.candidate_card import render_candidate_card
from utils.helpers import inject_global_css, empty_state, stage_color, source_icon

st.set_page_config(
    page_title="Candidates — The Sourcer",
    page_icon="👥",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.25rem 0 0.75rem;">
    <div style="font-size:1.5rem; font-weight:800; color:#F1F5F9;">👥 Candidate Database</div>
    <div style="color:#64748B; font-size:0.85rem; margin-top:3px;">
        Manage saved candidates, move them through your pipeline, and track outreach.
    </div>
</div>
""", unsafe_allow_html=True)

STAGES = ["sourced", "reviewed", "contacted", "responded", "interview", "rejected"]

# ── Load data ──────────────────────────────────────────────────────────────────
filter_search_id = st.session_state.pop("filter_search_id", None)
all_candidates   = get_candidates(user.id)
searches         = get_searches(user.id)

if not all_candidates:
    empty_state(
        "👥",
        "No candidates saved yet",
        "Run a search and save candidates to build your database.",
    )
    if st.button("🔍 Start a Search", type="primary"):
        st.switch_page("pages/04_New_Search.py")
    st.stop()

# ── View toggle + stats row ────────────────────────────────────────────────────
hdr1, hdr2 = st.columns([3, 2])
with hdr1:
    view_mode = st.radio(
        "View",
        ["🗂 Pipeline", "📋 List", "📊 Table"],
        horizontal=True,
        label_visibility="collapsed",
    )
with hdr2:
    # Mini stats
    stage_counts = {s: sum(1 for c in all_candidates if c.get("stage","sourced")==s) for s in STAGES}
    chips = "".join(
        f'<span style="background:{stage_color(s)}18; color:{stage_color(s)}; '
        f'border-radius:6px; padding:3px 9px; font-size:11px; font-weight:600; margin-right:4px;">'
        f'{s.title()} {stage_counts[s]}</span>'
        for s in STAGES if stage_counts[s] > 0
    )
    st.markdown(f'<div style="padding-top:6px;">{chips}</div>', unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔽 Filters & Search", expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        stage_filter = st.multiselect(
            "Stage",
            STAGES,
            default=[s for s in STAGES if s != "rejected"],
            format_func=lambda x: x.title(),
        )
    with fc2:
        source_opts   = sorted(set(c.get("source","Unknown") for c in all_candidates))
        source_filter = st.multiselect("Source", source_opts, default=source_opts)
    with fc3:
        search_opts   = {"All searches": None}
        for s in searches:
            search_opts[s.get("name","Unnamed")] = s.get("id")
        sel_search_lbl  = st.selectbox("Search", list(search_opts.keys()))
        sel_search_id   = filter_search_id or search_opts[sel_search_lbl]
    with fc4:
        min_score_db = st.slider("Min Match Score", 0, 100, 0, 5)

    name_q = st.text_input("🔎 Filter by name or skill", placeholder="Type to filter…")

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = all_candidates
if stage_filter:
    filtered = [c for c in filtered if c.get("stage","sourced") in stage_filter]
if source_filter:
    filtered = [c for c in filtered if c.get("source","") in source_filter]
if sel_search_id:
    filtered = [c for c in filtered if c.get("search_id") == sel_search_id]
if min_score_db:
    filtered = [c for c in filtered if c.get("match_score",0) >= min_score_db]
if name_q:
    q = name_q.lower()
    filtered = [c for c in filtered
                if q in (c.get("full_name") or "").lower()
                or any(q in s.lower() for s in (c.get("skills") or []))]

st.markdown(
    f'<div style="color:#475569; font-size:0.78rem; margin:6px 0 10px;">'
    f'{len(filtered)} candidates · {len(all_candidates)} total saved</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🗂 Pipeline":
    pipe_cols = st.columns(len(STAGES))

    for col_idx, stage in enumerate(STAGES):
        with pipe_cols[col_idx]:
            sc   = stage_color(stage)
            cands = [c for c in filtered if c.get("stage","sourced") == stage]

            # Column header
            st.markdown(f"""
            <div style="background:{sc}18; border:1px solid {sc}35;
                        border-radius:10px; padding:8px 10px; margin-bottom:10px; text-align:center;">
                <div style="font-weight:700; color:{sc}; font-size:0.78rem;
                            text-transform:uppercase; letter-spacing:0.06em;">
                    {stage.title()}
                </div>
                <div style="font-size:1.3rem; font-weight:800; color:#F1F5F9; margin-top:2px;">
                    {len(cands)}
                </div>
            </div>
            """, unsafe_allow_html=True)

            for c in cands:
                c_id    = c.get("id")
                name    = c.get("full_name") or "Unknown"
                title   = (c.get("current_title") or "")[:32]
                score   = c.get("match_score", 0)
                url     = c.get("profile_url","")
                s_icon  = source_icon(c.get("source",""))
                cur_idx = STAGES.index(stage)

                # Card
                st.markdown(f"""
                <div style="background:#1E293B; border:1px solid #334155;
                            border-left:3px solid {sc}; border-radius:8px;
                            padding:9px 11px; margin-bottom:7px;">
                    <div style="font-weight:600; color:#F1F5F9; font-size:0.82rem;
                                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {name}
                    </div>
                    <div style="color:#475569; font-size:0.72rem; margin-top:2px;">
                        {s_icon} {title}{'…' if len(c.get('current_title',''))>32 else ''}
                    </div>
                    <div style="color:#14B8A6; font-size:0.78rem; font-weight:700; margin-top:4px;">
                        {score}% match
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                ba, bb, bc = st.columns(3)
                with ba:
                    if url:
                        st.link_button("🔗", url, use_container_width=True)
                    else:
                        st.markdown("")
                with bb:
                    if cur_idx < len(STAGES) - 1:
                        nxt = STAGES[cur_idx + 1]
                        if st.button("→", key=f"fwd_{c_id}",
                                     use_container_width=True, help=f"Move to {nxt.title()}"):
                            update_candidate_stage(c_id, nxt)
                            st.rerun()
                with bc:
                    if st.button("👁", key=f"vpipe_{c_id}",
                                 use_container_width=True, help="View full profile"):
                        st.session_state["view_candidate"] = c
                        st.switch_page("pages/12_Candidate_Profile.py")

# ══════════════════════════════════════════════════════════════════════════════
# LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📋 List":
    # Export button
    exp_col, _ = st.columns([1, 5])
    with exp_col:
        if filtered:
            csv_df = pd.DataFrame([{
                "Name":        c.get("full_name",""),
                "Title":       c.get("current_title",""),
                "Location":    c.get("location",""),
                "Source":      c.get("source",""),
                "Match Score": c.get("match_score",0),
                "Stage":       c.get("stage",""),
                "Skills":      ", ".join(c.get("skills") or []),
                "Profile URL": c.get("profile_url",""),
            } for c in filtered])
            st.download_button(
                "📥 Export CSV",
                csv_df.to_csv(index=False),
                file_name="candidates.csv",
                mime="text/csv",
                use_container_width=True,
            )

    for i, candidate in enumerate(filtered):
        c_id          = candidate.get("id")
        current_stage = candidate.get("stage","sourced")

        card_col, ctrl_col = st.columns([4, 1])
        with card_col:
            render_candidate_card(
                candidate,
                idx=f"list_{i}",
                show_save_button=False,
                show_stage=True,
            )
        with ctrl_col:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            new_stage = st.selectbox(
                "Stage",
                STAGES,
                index=STAGES.index(current_stage) if current_stage in STAGES else 0,
                key=f"stg_{c_id}",
                format_func=lambda x: x.title(),
                label_visibility="collapsed",
            )
            if new_stage != current_stage:
                update_candidate_stage(c_id, new_stage)
                st.rerun()

            existing_notes = candidate.get("notes") or ""
            new_notes = st.text_area(
                "Notes",
                value=existing_notes,
                key=f"notes_{c_id}",
                height=72,
                placeholder="Add notes…",
                label_visibility="collapsed",
            )
            if new_notes != existing_notes:
                update_candidate_notes(c_id, new_notes)

            btn_a, btn_b = st.columns(2)
            with btn_a:
                if st.button("👁", key=f"vlist_{c_id}",
                             use_container_width=True, help="View profile"):
                    st.session_state["view_candidate"] = candidate
                    st.switch_page("pages/12_Candidate_Profile.py")
            with btn_b:
                if st.button("🗑", key=f"del_{c_id}",
                             use_container_width=True, help="Remove"):
                    delete_candidate(c_id)
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📊 Table":
    df = pd.DataFrame([{
        "Name":     c.get("full_name",""),
        "Title":    c.get("current_title",""),
        "Location": c.get("location",""),
        "Source":   c.get("source",""),
        "Score %":  c.get("match_score",0),
        "Stage":    (c.get("stage","sourced") or "sourced").title(),
        "Skills":   ", ".join((c.get("skills") or [])[:4]),
        "Profile":  c.get("profile_url",""),
    } for c in filtered])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score %":  st.column_config.NumberColumn("Score %", format="%d%%"),
            "Profile":  st.column_config.LinkColumn("Profile", display_text="Open →"),
        },
    )

    tbl_col1, tbl_col2 = st.columns([1, 5])
    with tbl_col1:
        st.download_button(
            "📥 Export CSV",
            df.to_csv(index=False),
            file_name="candidates.csv",
            mime="text/csv",
            use_container_width=True,
        )
