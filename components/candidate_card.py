"""
components/candidate_card.py
Reusable candidate profile card component.
"""
import streamlit as st
from utils.helpers import (
    score_color_class, score_label, format_skills_pills,
    source_icon, stage_color
)


def render_candidate_card(
    candidate: dict,
    idx,
    show_save_button: bool = True,
    show_stage: bool = False,
    on_save=None,
    on_outreach=None,
    show_profile_link: bool = True,
):
    """
    Render a candidate profile card.
    Returns True if save button was clicked.
    """
    score     = candidate.get("match_score", 0)
    name      = candidate.get("full_name") or "Unknown"
    title     = candidate.get("current_title") or ""
    location  = candidate.get("location") or ""
    source    = candidate.get("source") or ""
    url       = candidate.get("profile_url") or ""
    summary   = candidate.get("summary") or ""
    skills    = candidate.get("skills") or []
    stage     = candidate.get("stage", "sourced")
    s_icon    = source_icon(source)
    score_cls = score_color_class(score)
    score_lbl = score_label(score)
    rec       = candidate.get("recommendation", "")
    sc        = stage_color(stage)

    rec_colors = {
        "strong_match": "#10B981",
        "good_match":   "#14B8A6",
        "potential":    "#F59E0B",
        "weak_match":   "#F87171",
    }
    border_color = rec_colors.get(rec, "#334155")

    # ── Card HTML ──────────────────────────────────────────────────────────────
    stage_badge = (
        f'<span style="font-size:11px; background:{sc}20; border:1px solid {sc}40; '
        f'border-radius:999px; padding:2px 10px; color:{sc}; margin-left:6px;">'
        f'{stage.title()}</span>'
    ) if show_stage else ""

    st.markdown(f"""
    <div class="candidate-card" style="border-left:3px solid {border_color};">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div style="flex:1; min-width:0;">
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">
                    <span style="font-size:1rem; font-weight:700; color:#F1F5F9;">{name}</span>
                    <span style="font-size:11px; background:#1E293B; border:1px solid #334155;
                          border-radius:999px; padding:2px 10px; color:#64748B;">
                        {s_icon} {source}
                    </span>
                    {stage_badge}
                </div>
                <div style="color:#64748B; font-size:0.85rem; margin-top:4px;">
                    {title}{"  ·  📍 " + location if location else ""}
                </div>
                <div style="margin-top:8px; font-size:0.8rem; color:#475569; line-height:1.5;">
                    {(summary[:200] + "…") if summary and len(summary) > 200 else summary}
                </div>
                <div style="margin-top:10px;">
                    {format_skills_pills(skills, max_show=6)}
                </div>
            </div>
            <div style="text-align:right; flex-shrink:0; min-width:72px;">
                <div class="match-score {score_cls}" style="font-size:1.8rem; font-weight:800; line-height:1;">
                    {score}%
                </div>
                <div style="font-size:10px; color:{border_color}; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.04em; margin-top:2px;">
                    {score_lbl}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Action row ─────────────────────────────────────────────────────────────
    saved = False
    btn_count = sum([bool(url and show_profile_link), show_save_button, True, True])  # profile, save, outreach, view
    cols = st.columns(4)

    with cols[0]:
        if url and show_profile_link:
            st.link_button("🔗 Profile", url, use_container_width=True)

    with cols[1]:
        if show_save_button:
            if st.button("💾 Save", key=f"save_{idx}", use_container_width=True):
                saved = True
                if on_save:
                    on_save(candidate)

    with cols[2]:
        if st.button("✉️ Outreach", key=f"out_{idx}", use_container_width=True):
            st.session_state["outreach_candidate"] = candidate
            if on_outreach:
                on_outreach(candidate)
            else:
                st.switch_page("pages/08_Outreach.py")

    with cols[3]:
        if st.button("👁 View", key=f"view_{idx}", use_container_width=True):
            st.session_state["view_candidate"] = candidate
            st.switch_page("pages/12_Candidate_Profile.py")

    # ── AI Rationale expander ──────────────────────────────────────────────────
    rationale = candidate.get("ai_rationale", "")
    matched   = candidate.get("matched_skills", [])
    missing   = candidate.get("missing_skills", [])

    if rationale or matched or missing:
        with st.expander("🧠 AI Analysis", expanded=False):
            if rationale:
                st.markdown(f"**Assessment:** {rationale}")
            c1, c2 = st.columns(2)
            with c1:
                if matched:
                    st.markdown("**✅ Matched**")
                    for s in matched[:5]:
                        st.markdown(f"- {s}")
            with c2:
                if missing:
                    st.markdown("**⚠️ Missing**")
                    for s in missing[:5]:
                        st.markdown(f"- {s}")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    return saved
