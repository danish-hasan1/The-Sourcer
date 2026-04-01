import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/08_Outreach.py — AI-Powered Outreach
Full rebuild: better candidate picker, character counter, copy flow.
"""
import streamlit as st
from core.auth import require_auth, load_user_session, get_anthropic_key
from core.ai_engine import generate_outreach
from core.database import get_candidates, save_outreach, get_outreach_log
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state, source_icon

st.set_page_config(
    page_title="Outreach — The Sourcer",
    page_icon="✉️",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.25rem 0 0.75rem;">
    <div style="font-size:1.5rem; font-weight:800; color:#F1F5F9;">✉️ Outreach</div>
    <div style="color:#64748B; font-size:0.85rem; margin-top:3px;">
        Generate personalised messages for candidates — then copy and send.
    </div>
</div>
""", unsafe_allow_html=True)

anthropic_key = get_anthropic_key()
if not anthropic_key:
    st.error("🔑 Anthropic API key required. Go to Settings.")
    if st.button("⚙️ Settings"):
        st.switch_page("pages/09_Settings.py")
    st.stop()

tab_draft, tab_log = st.tabs(["✍️ Draft Message", "📋 Outreach Log"])

# ══════════════════════════════════════════════════════════════════════════════
# DRAFT TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_draft:
    left, right = st.columns([2, 3], gap="large")

    with left:
        st.markdown("### 1 · Select Candidate")

        preselected = st.session_state.get("outreach_candidate")
        candidates  = get_candidates(user.id)

        if not candidates and not preselected:
            empty_state("👥", "No saved candidates",
                        "Save candidates from search results first.")
            st.stop()

        # Build option map — preselected first
        cand_map = {}
        if preselected:
            lbl = (f"{preselected.get('full_name','Unknown')} — "
                   f"{preselected.get('current_title','')}")
            cand_map[lbl] = preselected

        for c in candidates:
            lbl = (f"{c.get('full_name','Unknown')} — "
                   f"{c.get('current_title','')} "
                   f"({source_icon(c.get('source',''))} {c.get('source','')})")
            if lbl not in cand_map:
                cand_map[lbl] = c

        sel_label = st.selectbox(
            "Candidate",
            options=list(cand_map.keys()),
            label_visibility="collapsed",
        )
        candidate = cand_map[sel_label]

        # Mini card
        score = candidate.get("match_score", 0)
        sc_color = "#10B981" if score >= 80 else "#14B8A6" if score >= 65 else "#F59E0B" if score >= 45 else "#F87171"
        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                    padding:14px 16px; margin-top:8px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-weight:700; color:#F1F5F9; font-size:0.92rem;">
                        {candidate.get('full_name','Unknown')}
                    </div>
                    <div style="color:#64748B; font-size:0.78rem; margin-top:2px;">
                        {candidate.get('current_title','')}
                    </div>
                    <div style="color:#475569; font-size:0.72rem; margin-top:3px;">
                        {source_icon(candidate.get('source',''))} {candidate.get('source','')}
                        {'  ·  📍 ' + candidate.get('location','') if candidate.get('location') else ''}
                    </div>
                    <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:3px;">
                        {''.join(
                            f"<span style='background:#0F172A;border:1px solid #1E293B;"
                            f"border-radius:999px;padding:2px 8px;font-size:10px;color:#64748B;'>{s}</span>"
                            for s in (candidate.get('skills') or [])[:5]
                        )}
                    </div>
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    <div style="font-size:1.4rem; font-weight:800; color:{sc_color};">{score}%</div>
                    <div style="font-size:10px; color:#475569;">match</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        url = candidate.get("profile_url","")
        if url:
            st.link_button("🔗 View Profile", url, use_container_width=True)

        st.markdown("---")
        st.markdown("### 2 · Message Settings")

        fmt = st.radio(
            "Format",
            ["LinkedIn Connection Note", "LinkedIn InMail", "Email"],
            help=(
                "Connection Note: max 300 chars · "
                "InMail: up to 2000 chars · "
                "Email: full length"
            ),
        )
        tone = st.select_slider(
            "Tone",
            options=["Formal", "Professional", "Conversational", "Casual"],
            value="Professional",
        )
        jd_summary = st.text_area(
            "Role context (optional)",
            value=st.session_state.get("outreach_jd_summary",""),
            placeholder="Brief description of the role — helps personalise the message…",
            height=90,
        )
        generate_btn = st.button(
            "✨ Generate Message",
            type="primary",
            use_container_width=True,
        )

    # ── Right: generated message ───────────────────────────────────────────────
    with right:
        st.markdown("### 3 · Your Personalised Message")

        FMT_MAP = {
            "LinkedIn Connection Note": "linkedin",
            "LinkedIn InMail":          "linkedin_inmail",
            "Email":                    "email",
        }
        CHAR_LIMITS = {
            "LinkedIn Connection Note": 300,
            "LinkedIn InMail":          2000,
            "Email":                    None,
        }

        if "generated_msg"     not in st.session_state: st.session_state.generated_msg     = None
        if "generated_subject" not in st.session_state: st.session_state.generated_subject = None

        if generate_btn:
            with st.spinner("🤖 Crafting your personalised message…"):
                result = generate_outreach(
                    api_key=anthropic_key,
                    candidate=candidate,
                    jd_summary=jd_summary,
                    tone=tone.lower(),
                    fmt=FMT_MAP.get(fmt,"linkedin"),
                )
            if result:
                st.session_state.generated_msg     = result.get("message","")
                st.session_state.generated_subject = result.get("subject")
            else:
                st.error("Message generation failed — check your API key.")

        msg = st.session_state.generated_msg

        if msg:
            if st.session_state.generated_subject:
                st.markdown(f"""
                <div style="background:#1E293B; border:1px solid #334155; border-radius:8px;
                            padding:10px 14px; margin-bottom:10px; font-size:0.85rem;">
                    <span style="color:#475569;">Subject: </span>
                    <span style="color:#F1F5F9; font-weight:600;">{st.session_state.generated_subject}</span>
                </div>
                """, unsafe_allow_html=True)

            edited = st.text_area(
                "Edit before sending",
                value=msg,
                height=300,
                label_visibility="collapsed",
            )

            # Character counter
            char_n = len(edited)
            limit  = CHAR_LIMITS.get(fmt)
            if limit:
                pct   = char_n / limit
                color = "#10B981" if pct <= 0.8 else "#F59E0B" if pct <= 1.0 else "#F87171"
                bar   = min(int(pct * 100), 100)
                st.markdown(f"""
                <div style="margin-top:4px;">
                    <div style="display:flex; justify-content:space-between;
                                font-size:0.72rem; color:#475569; margin-bottom:3px;">
                        <span>{char_n} / {limit} characters</span>
                        <span style="color:{color};">
                            {'✅ Good length' if pct <= 0.8 else '⚠️ Getting long' if pct <= 1.0 else '❌ Too long — trim it'}
                        </span>
                    </div>
                    <div style="background:#0F172A; border-radius:999px; height:4px; overflow:hidden;">
                        <div style="background:{color}; width:{bar}%; height:100%;
                                    border-radius:999px; transition:width 0.3s;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="font-size:0.72rem; color:#475569; margin-top:3px;">'
                    f'{char_n} characters</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            act1, act2, act3 = st.columns(3)

            with act1:
                # JS clipboard copy
                if st.button("📋 Copy Message", use_container_width=True, type="primary"):
                    # Escape for JS string
                    escaped = edited.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                    st.markdown(
                        f"<script>navigator.clipboard.writeText(`{escaped}`);</script>",
                        unsafe_allow_html=True,
                    )
                    st.toast("📋 Copied to clipboard!", icon="✅")
                    save_outreach(
                        user_id=user.id,
                        candidate_id=candidate.get("id"),
                        message=edited,
                        fmt=FMT_MAP.get(fmt,"linkedin"),
                        tone=tone.lower(),
                    )

            with act2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.generated_msg     = None
                    st.session_state.generated_subject = None
                    st.rerun()

            with act3:
                if url:
                    st.link_button("🔗 Open Profile", url, use_container_width=True)

            # Sending tips
            tips = {
                "LinkedIn Connection Note": (
                    "1. Open their LinkedIn profile\n"
                    "2. Click **Connect**\n"
                    "3. Click **Add a note**\n"
                    "4. Paste and send"
                ),
                "LinkedIn InMail": (
                    "1. Open their profile\n"
                    "2. Click **Message** (requires Premium/Recruiter)\n"
                    "3. Paste subject and body"
                ),
                "Email": (
                    "1. Find their email in the profile bio or company website\n"
                    "2. Open your email client\n"
                    "3. Paste subject and body"
                ),
            }
            with st.expander("💡 How to send this", expanded=False):
                st.markdown(tips.get(fmt,""))

        else:
            # Empty state
            st.markdown("""
            <div style="background:#1E293B; border:2px dashed #1E293B;
                        border-radius:14px; padding:4rem 2rem; text-align:center; margin-top:1rem;">
                <div style="font-size:2.5rem; margin-bottom:1rem;">✉️</div>
                <div style="font-weight:600; color:#F1F5F9; margin-bottom:6px;">
                    Your message will appear here
                </div>
                <div style="color:#334155; font-size:0.83rem;">
                    Select a candidate and click Generate Message
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LOG TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    log = get_outreach_log(user.id)

    if not log:
        empty_state("📋", "No outreach messages yet",
                    "Generated messages will be logged here automatically.")
    else:
        st.markdown(
            f'<div style="color:#475569; font-size:0.78rem; margin-bottom:1rem;">'
            f'{len(log)} messages sent</div>',
            unsafe_allow_html=True,
        )
        for entry in log:
            ci   = entry.get("candidates") or {}
            cname = ci.get("full_name","Unknown") if isinstance(ci, dict) else "Unknown"
            ctitle = ci.get("current_title","") if isinstance(ci, dict) else ""
            sent   = (entry.get("created_at") or "")[:10]
            fmt_l  = (entry.get("message_format") or "linkedin").replace("_"," ").title()
            tone_l = (entry.get("tone") or "professional").title()

            with st.expander(f"✉️ {cname}  ·  {fmt_l}  ·  {sent}", expanded=False):
                st.markdown(f"**To:** {cname}  ·  {ctitle}")
                st.markdown(f"**Format:** {fmt_l}  ·  **Tone:** {tone_l}")
                st.markdown("---")
                st.text_area(
                    "Message",
                    value=entry.get("message_text",""),
                    height=180,
                    key=f"log_{entry.get('id')}",
                    disabled=True,
                    label_visibility="collapsed",
                )
