import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/08_Outreach.py — AI-Powered Outreach
"""
import streamlit as st
from core.auth import require_auth, load_user_session, get_anthropic_key
from core.ai_engine import generate_outreach
from core.database import get_candidates, save_outreach, get_outreach_log
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state, source_icon

st.set_page_config(page_title="Outreach — The Sourcer", page_icon="✉️", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">✉️ Outreach</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Generate personalised outreach messages for candidates — then copy and send.
    </div>
</div>
""", unsafe_allow_html=True)

anthropic_key = get_anthropic_key()
if not anthropic_key:
    st.error("🔑 Anthropic API key required. Go to Settings.")
    if st.button("⚙️ Settings"):
        st.switch_page("pages/09_Settings.py")
    st.stop()

tab1, tab2 = st.tabs(["✍️ Draft Message", "📋 Outreach Log"])

# ── DRAFT MESSAGE ──────────────────────────────────────────────────────────────
with tab1:
    left, right = st.columns([2, 3], gap="large")

    with left:
        st.markdown("### 1. Select Candidate")

        # Check if candidate was passed from search results or database
        preselected = st.session_state.get("outreach_candidate")

        candidates = get_candidates(user.id)
        if not candidates and not preselected:
            empty_state("👥", "No saved candidates", "Save candidates first from search results.")
            st.stop()

        # Build candidate options
        cand_options = {}
        if preselected:
            label = f"{preselected.get('full_name', 'Unknown')} — {preselected.get('current_title', '')}"
            cand_options[label] = preselected

        for c in candidates:
            label = f"{c.get('full_name', 'Unknown')} — {c.get('current_title', '')} ({source_icon(c.get('source',''))} {c.get('source','')})"
            cand_options[label] = c

        selected_label = st.selectbox(
            "Choose candidate",
            options=list(cand_options.keys()),
            label_visibility="collapsed",
        )
        candidate = cand_options[selected_label]

        # Show candidate mini card
        st.markdown(f"""
        <div style="background:#1E293B; border:1px solid #334155; border-radius:10px; padding:14px; margin-top:8px;">
            <div style="font-weight:700; color:#F1F5F9;">{candidate.get('full_name','Unknown')}</div>
            <div style="color:#94A3B8; font-size:0.82rem; margin-top:3px;">{candidate.get('current_title','')}</div>
            <div style="color:#64748B; font-size:0.78rem; margin-top:2px;">
                {source_icon(candidate.get('source',''))} {candidate.get('source','')}
                {' · 📍 ' + candidate.get('location','') if candidate.get('location') else ''}
            </div>
            <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:4px;">
                {''.join(f'<span style="background:#0F172A;border:1px solid #334155;border-radius:999px;padding:2px 8px;font-size:10px;color:#94A3B8;">{s}</span>' for s in (candidate.get('skills') or [])[:5])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 2. Message Settings")

        fmt = st.radio(
            "Format",
            ["LinkedIn Message", "LinkedIn InMail", "Email"],
            horizontal=False,
        )
        tone = st.select_slider(
            "Tone",
            options=["Formal", "Professional", "Conversational", "Casual"],
            value="Professional",
        )

        jd_summary = st.text_area(
            "Role summary (optional)",
            value=st.session_state.get("outreach_jd_summary", ""),
            placeholder="Brief summary of the role you're hiring for...",
            height=100,
        )

        generate_btn = st.button("✨ Generate Message", type="primary", use_container_width=True)

    with right:
        st.markdown("### 3. Your Personalised Message")

        fmt_map = {
            "LinkedIn Message": "linkedin",
            "LinkedIn InMail": "linkedin_inmail",
            "Email": "email",
        }

        if "generated_message" not in st.session_state:
            st.session_state.generated_message = None
        if "generated_subject" not in st.session_state:
            st.session_state.generated_subject = None

        if generate_btn:
            with st.spinner("🤖 Crafting your personalised message..."):
                result = generate_outreach(
                    api_key=anthropic_key,
                    candidate=candidate,
                    jd_summary=jd_summary,
                    tone=tone.lower(),
                    fmt=fmt_map.get(fmt, "linkedin"),
                )
            if result:
                st.session_state.generated_message = result.get("message", "")
                st.session_state.generated_subject = result.get("subject")
                st.session_state.generated_char_count = result.get("character_count", 0)

        if st.session_state.generated_message:
            msg = st.session_state.generated_message
            subject = st.session_state.generated_subject
            char_count = st.session_state.get("generated_char_count", 0)

            if subject:
                st.markdown(f"**Subject:** {subject}")
                st.markdown("---")

            # Editable message
            edited_msg = st.text_area(
                "Edit before sending",
                value=msg,
                height=320,
                label_visibility="collapsed",
            )

            # Stats row
            char_display = len(edited_msg)
            if "linkedin" in fmt.lower() and "inmail" not in fmt.lower():
                limit = 300
                color = "#10B981" if char_display <= limit else "#F87171"
                st.markdown(f'<div style="font-size:0.78rem; color:{color};">{char_display}/{limit} characters</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:0.78rem; color:#64748B;">{char_display} characters</div>', unsafe_allow_html=True)

            st.markdown("---")
            act1, act2, act3 = st.columns(3)

            with act1:
                if st.button("📋 Copy Message", use_container_width=True, type="primary"):
                    st.markdown(f"""
                    <script>
                    navigator.clipboard.writeText({repr(edited_msg)});
                    </script>
                    """, unsafe_allow_html=True)
                    st.toast("✅ Copied to clipboard!", icon="📋")
                    # Save to outreach log
                    save_outreach(
                        user_id=user.id,
                        candidate_id=candidate.get("id"),
                        message=edited_msg,
                        fmt=fmt_map.get(fmt, "linkedin"),
                        tone=tone.lower(),
                    )

            with act2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.generated_message = None
                    st.rerun()

            with act3:
                url = candidate.get("profile_url", "")
                if url:
                    st.link_button("🔗 Open Profile", url, use_container_width=True)

            # Tips
            st.markdown("""---
**💡 Sending Tips**
- **LinkedIn Message:** Go to their profile → Message → Paste
- **InMail:** Available via LinkedIn Premium → InMail button
- **Email:** Look for email in their profile bio/website
""")
        else:
            st.markdown("""
            <div style="background:#1E293B; border:1px dashed #334155; border-radius:12px; padding:3rem 2rem; text-align:center;">
                <div style="font-size:2rem; margin-bottom:1rem;">✉️</div>
                <div style="color:#F1F5F9; font-weight:600;">Your message will appear here</div>
                <div style="color:#64748B; font-size:0.85rem; margin-top:8px;">Select a candidate and click Generate Message</div>
            </div>
            """, unsafe_allow_html=True)

# ── OUTREACH LOG ──────────────────────────────────────────────────────────────
with tab2:
    log = get_outreach_log(user.id)

    if not log:
        empty_state("📋", "No outreach sent yet", "Generated messages will appear here.")
    else:
        for entry in log:
            cand_info = entry.get("candidates") or {}
            cand_name = cand_info.get("full_name", "Unknown") if isinstance(cand_info, dict) else "Unknown"
            cand_title = cand_info.get("current_title", "") if isinstance(cand_info, dict) else ""
            sent_at = entry.get("created_at", "")[:10] if entry.get("created_at") else ""
            fmt_label = entry.get("message_format", "linkedin").replace("_", " ").title()
            tone_label = entry.get("tone", "professional").title()

            with st.expander(f"✉️ {cand_name} — {fmt_label} · {sent_at}", expanded=False):
                st.markdown(f"**To:** {cand_name} · {cand_title}")
                st.markdown(f"**Format:** {fmt_label} · **Tone:** {tone_label}")
                st.markdown("---")
                st.text_area("Message", value=entry.get("message_text", ""), height=200,
                             key=f"log_{entry.get('id')}", disabled=True, label_visibility="collapsed")
