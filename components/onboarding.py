"""
components/onboarding.py
First-time user onboarding tutorial overlay.
"""
import streamlit as st
from core.database import get_onboarding, mark_onboarding_complete, complete_onboarding_step


ONBOARDING_STEPS = [
    {
        "id": "welcome",
        "icon": "👋",
        "title": "Welcome to The Sourcer",
        "body": "Your AI-powered talent intelligence platform. We'll help you find the best candidates across the entire internet — LinkedIn, GitHub, Stack Overflow, and leading job boards worldwide.",
        "cta": "Get Started →"
    },
    {
        "id": "api_keys",
        "icon": "🔑",
        "title": "Add Your API Keys",
        "body": "The Sourcer uses your own API keys so you stay in full control. You'll need:\n\n• **Anthropic API key** — Powers AI analysis of job descriptions\n• **Google Custom Search API** — Enables X-Ray sourcing across platforms\n• **GitHub Token** (optional) — Increases search limits for developer sourcing\n\nAll keys are stored securely and never shared.",
        "cta": "Go to Settings →",
        "action": "settings"
    },
    {
        "id": "new_search",
        "icon": "🔍",
        "title": "Start With a Job Description",
        "body": "Paste any job description and hit **Analyse & Source**. Our AI will:\n\n1. Understand the hiring intent (not just keywords)\n2. Build a weighted skill scoring matrix\n3. Generate optimised Boolean search strings\n4. Auto-populate all search filters for you\n\nYou can tweak any filter before running the search.",
        "cta": "Create First Search →",
        "action": "search"
    },
    {
        "id": "sources",
        "icon": "🌐",
        "title": "Search Everywhere at Once",
        "body": "The Sourcer searches across:\n\n• 🔵 LinkedIn profiles via Google X-Ray\n• 🐙 GitHub developer profiles\n• 📚 Stack Overflow experts\n• 📋 Regional job boards (Naukri, Reed, InfoJobs & more)\n• 📄 CVs published on the open web\n\nAll results are deduplicated and AI-scored.",
        "cta": "Understood →"
    },
    {
        "id": "pipeline",
        "icon": "📊",
        "title": "Manage Your Pipeline",
        "body": "Every candidate you save moves through your pipeline:\n\n**Sourced → Reviewed → Contacted → Responded → Interview**\n\nDraft outreach messages with one click, add notes, and collaborate with your team.",
        "cta": "Let's Go! 🚀",
        "action": "done"
    }
]


def render_onboarding():
    """Show the onboarding tutorial if not completed. Returns True if onboarding is active."""
    user = st.session_state.get("user")
    if not user:
        return False

    profile = st.session_state.get("profile", {})
    if profile.get("onboarding_completed"):
        return False

    # Get or init step
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 0

    step_idx = st.session_state.onboarding_step
    if step_idx >= len(ONBOARDING_STEPS):
        return False

    step = ONBOARDING_STEPS[step_idx]
    total = len(ONBOARDING_STEPS)

    # Overlay backdrop
    st.markdown("""
    <style>
    .onboarding-overlay {
        position: fixed; inset: 0; z-index: 9999;
        background: rgba(0,0,0,0.75);
        display: flex; align-items: center; justify-content: center;
    }
    .onboarding-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 2.5rem;
        max-width: 520px;
        width: 90%;
        box-shadow: 0 25px 60px rgba(0,0,0,0.5);
        text-align: center;
    }
    .onboarding-icon { font-size: 3rem; margin-bottom: 1rem; }
    .onboarding-title { font-size: 1.4rem; font-weight: 700; color: #F1F5F9; margin-bottom: 1rem; }
    .onboarding-body { color: #94A3B8; font-size: 0.9rem; line-height: 1.7; white-space: pre-line; margin-bottom: 1.5rem; text-align: left; }
    .onboarding-progress { font-size: 0.75rem; color: #475569; margin-top: 1rem; }
    .onboarding-dots { display: flex; gap: 6px; justify-content: center; margin-bottom: 1.5rem; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #334155; }
    .dot.active { background: #0D9488; }
    </style>
    """, unsafe_allow_html=True)

    dots = "".join(
        f'<div class="dot{"" if i != step_idx else " active"}"></div>'
        for i in range(total)
    )

    st.markdown(f"""
    <div class="onboarding-overlay">
        <div class="onboarding-card">
            <div class="onboarding-icon">{step['icon']}</div>
            <div class="onboarding-title">{step['title']}</div>
            <div class="onboarding-body">{step['body']}</div>
            <div class="onboarding-dots">{dots}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Use actual Streamlit buttons below the overlay
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if step_idx < total - 1:
            if st.button(step.get("cta", "Next →"), use_container_width=True, type="primary"):
                st.session_state.onboarding_step += 1
                action = step.get("action")
                complete_onboarding_step(user.id, step["id"])
                if action == "settings":
                    st.session_state.onboarding_step += 1  # Skip to next step after redirect
                st.rerun()

            skip_col1, skip_col2 = st.columns(2)
            with skip_col2:
                if st.button("Skip Tutorial", use_container_width=True):
                    _complete_onboarding()
        else:
            if st.button("🚀  Start Sourcing!", use_container_width=True, type="primary"):
                _complete_onboarding()

    return True


def _complete_onboarding():
    user = st.session_state.get("user")
    if user:
        mark_onboarding_complete(user.id)
        if "profile" in st.session_state:
            st.session_state.profile["onboarding_completed"] = True
    st.session_state.onboarding_step = len(ONBOARDING_STEPS)
    st.rerun()
