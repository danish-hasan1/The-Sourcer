"""
pages/12_Candidate_Profile.py — Single Candidate Deep View
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.auth import require_auth, load_user_session
from core.database import update_candidate_stage, update_candidate_notes, save_outreach
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, score_color_class, score_label, stage_color, source_icon, format_skills_pills

st.set_page_config(
    page_title="Candidate Profile — The Sourcer",
    page_icon="👤",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

# ── Get candidate from session ─────────────────────────────────────────────────
candidate = st.session_state.get("view_candidate")

if not candidate:
    st.warning("No candidate selected. Go to Candidate Database to view a profile.")
    if st.button("← Back to Database"):
        st.switch_page("pages/06_Candidate_Database.py")
    st.stop()

c_id     = candidate.get("id")
name     = candidate.get("full_name") or "Unknown"
title    = candidate.get("current_title") or ""
location = candidate.get("location") or ""
source   = candidate.get("source") or ""
url      = candidate.get("profile_url") or ""
skills   = candidate.get("skills") or []
score    = candidate.get("match_score", 0)
summary  = candidate.get("summary") or ""
stage    = candidate.get("stage", "sourced")
notes    = candidate.get("notes") or ""
email    = candidate.get("email") or ""
matched  = candidate.get("matched_skills") or []
missing  = candidate.get("missing_skills") or []
rationale = candidate.get("ai_rationale") or ""

score_cls = score_color_class(score)
score_lbl = score_label(score)
sc        = stage_color(stage)
s_icon    = source_icon(source)

# ── Back button ────────────────────────────────────────────────────────────────
if st.button("← Back to Database", key="back_top"):
    st.switch_page("pages/06_Candidate_Database.py")

st.markdown("---")

# ── Hero section ───────────────────────────────────────────────────────────────
left_hero, right_hero = st.columns([3, 1], gap="large")

with left_hero:
    st.markdown(f"""
    <div style="display:flex; align-items:flex-start; gap:20px; margin-bottom:1.5rem;">
        <div style="width:64px; height:64px; border-radius:50%;
                    background:linear-gradient(135deg, #0D9488, #F59E0B);
                    display:flex; align-items:center; justify-content:center;
                    font-size:1.6rem; font-weight:800; color:white; flex-shrink:0;">
            {name[0].upper() if name else "?"}
        </div>
        <div>
            <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">{name}</div>
            <div style="color:#94A3B8; font-size:1rem; margin-top:4px;">{title}</div>
            <div style="display:flex; gap:16px; margin-top:8px; flex-wrap:wrap;">
                {"<span style='color:#64748B; font-size:0.85rem;'>📍 " + location + "</span>" if location else ""}
                <span style="color:#64748B; font-size:0.85rem;">{s_icon} {source}</span>
                {"<span style='color:#64748B; font-size:0.85rem;'>✉️ " + email + "</span>" if email else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Skills
    if skills:
        st.markdown(format_skills_pills(skills, max_show=12), unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Summary
    if summary:
        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:14px 18px; margin-top:12px;">
            <div style="font-size:0.85rem; color:#94A3B8; line-height:1.7;">{summary}</div>
        </div>
        """, unsafe_allow_html=True)

with right_hero:
    # Match score
    st.markdown(f"""
    <div style="background:#1E293B; border:1px solid #334155; border-radius:12px; padding:20px; text-align:center; margin-bottom:12px;">
        <div style="font-size:0.7rem; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">AI Match Score</div>
        <div class="match-score {score_cls}" style="font-size:2.5rem; font-weight:800;">{score}%</div>
        <div style="font-size:0.78rem; color:#94A3B8; margin-top:4px;">{score_lbl}</div>
    </div>
    """, unsafe_allow_html=True)

    # Stage
    st.markdown(f"""
    <div style="background:{sc}15; border:1px solid {sc}40; border-radius:10px; padding:12px; text-align:center; margin-bottom:12px;">
        <div style="font-size:0.7rem; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;">Pipeline Stage</div>
        <div style="font-weight:700; color:{sc}; text-transform:capitalize;">{stage}</div>
    </div>
    """, unsafe_allow_html=True)

    # Actions
    if url:
        st.link_button("🔗 View Profile", url, use_container_width=True)

    if st.button("✉️ Draft Outreach", use_container_width=True, type="primary"):
        st.session_state["outreach_candidate"] = candidate
        st.switch_page("pages/08_Outreach.py")

st.markdown("---")

# ── Lower section ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    # AI Analysis
    if rationale or matched or missing:
        st.markdown("### 🧠 AI Analysis")
        if rationale:
            st.markdown(f"""
            <div style="background:#1E293B; border-left:3px solid #0D9488; border-radius:0 8px 8px 0; padding:12px 16px; margin-bottom:1rem; font-size:0.88rem; color:#94A3B8; line-height:1.6;">
                {rationale}
            </div>
            """, unsafe_allow_html=True)

        mc1, mc2 = st.columns(2)
        with mc1:
            if matched:
                st.markdown("**✅ Matched Skills**")
                for s in matched:
                    st.markdown(f"- {s}")
        with mc2:
            if missing:
                st.markdown("**⚠️ Missing Skills**")
                for s in missing:
                    st.markdown(f"- {s}")
        st.markdown("---")

    # Notes
    st.markdown("### 📝 Notes")
    new_notes = st.text_area(
        "Add notes about this candidate",
        value=notes,
        height=140,
        placeholder="Interview notes, impressions, follow-up actions...",
        label_visibility="collapsed",
    )
    if new_notes != notes:
        if st.button("💾 Save Notes", type="primary"):
            update_candidate_notes(c_id, new_notes)
            st.session_state.view_candidate["notes"] = new_notes
            st.success("Notes saved!")

with col_right:
    st.markdown("### 🔄 Update Stage")
    STAGES = ["sourced", "reviewed", "contacted", "responded", "interview", "rejected"]
    current_idx = STAGES.index(stage) if stage in STAGES else 0
    new_stage = st.selectbox(
        "Pipeline Stage",
        STAGES,
        index=current_idx,
        label_visibility="collapsed",
        format_func=lambda x: x.title(),
    )
    if new_stage != stage:
        if st.button("Update Stage", use_container_width=True, type="primary"):
            update_candidate_stage(c_id, new_stage)
            st.session_state.view_candidate["stage"] = new_stage
            st.success(f"Moved to {new_stage.title()}!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔗 Quick Actions")

    raw = candidate.get("raw_data") or {}
    username = raw.get("username")
    if username and "GitHub" in source:
        st.link_button("🐙 GitHub Profile", f"https://github.com/{username}", use_container_width=True)
        repos = raw.get("top_repos", [])
        if repos:
            st.markdown("**Top Repos:**")
            for r in repos[:4]:
                st.markdown(f"- [`{r}`](https://github.com/{username}/{r})")

    so_id = raw.get("user_id")
    if so_id and "Stack" in source:
        st.link_button("📚 Stack Overflow Profile", f"https://stackoverflow.com/users/{so_id}", use_container_width=True)
        rep = raw.get("reputation", 0)
        if rep:
            st.metric("Reputation", f"{rep:,}")
