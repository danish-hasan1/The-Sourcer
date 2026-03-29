"""
app.py — The Sourcer Landing Page
Entry point for the application.
"""
import streamlit as st
from utils.helpers import inject_global_css

st.set_page_config(
    page_title="The Sourcer — AI Talent Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_css()

# Redirect authenticated users to dashboard
if "user" in st.session_state and st.session_state.user:
    st.switch_page("pages/03_Dashboard.py")

# ── Landing Page ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
.landing-hero {
    min-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 4rem 2rem;
    position: relative;
}
.hero-bg {
    position: fixed; inset: 0; z-index: -1;
    background: radial-gradient(ellipse 80% 60% at 50% 0%, rgba(13,148,136,0.15) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 80% 80%, rgba(245,158,11,0.08) 0%, transparent 50%),
                #0F172A;
}
.hero-tag {
    display: inline-block;
    background: rgba(13,148,136,0.15);
    border: 1px solid rgba(13,148,136,0.4);
    color: #14B8A6;
    border-radius: 999px;
    padding: 6px 18px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 800;
    color: #F1F5F9;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 1.5rem;
}
.hero-title .accent { color: #14B8A6; }
.hero-title .gold { color: #F59E0B; }
.hero-subtitle {
    font-size: 1.1rem;
    color: #94A3B8;
    max-width: 560px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    max-width: 1100px;
    margin: 4rem auto;
}
.feature-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
    text-align: left;
    transition: border-color 0.2s, transform 0.2s;
}
.feature-card:hover { border-color: #0D9488; transform: translateY(-2px); }
.feature-icon { font-size: 1.8rem; margin-bottom: 12px; }
.feature-title { font-size: 1rem; font-weight: 700; color: #F1F5F9; margin-bottom: 8px; }
.feature-desc { font-size: 0.83rem; color: #94A3B8; line-height: 1.6; }

.sources-bar {
    display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;
    margin: 2rem 0;
}
.source-chip {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 0.82rem;
    color: #94A3B8;
    font-weight: 500;
}

.stat-row {
    display: flex; gap: 40px; justify-content: center; flex-wrap: wrap;
    margin: 3rem 0;
}
.stat-item { text-align: center; }
.stat-value { font-size: 2rem; font-weight: 800; color: #14B8A6; }
.stat-label { font-size: 0.78rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; }
</style>
<div class="hero-bg"></div>
""", unsafe_allow_html=True)

# Hero
st.markdown("""
<div class="landing-hero">
    <div class="hero-tag">🎯 AI-Powered Talent Sourcing</div>
    <div class="hero-title">
        Find the <span class="accent">Right Candidates</span><br>
        Before Your <span class="gold">Competition Does</span>
    </div>
    <div class="hero-subtitle">
        The Sourcer searches LinkedIn, GitHub, Stack Overflow, and 15+ job boards simultaneously —
        powered by AI that understands your hiring intent, not just keywords.
    </div>
</div>
""", unsafe_allow_html=True)

# CTA Buttons
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("🚀  Start Sourcing Free", use_container_width=True, type="primary"):
        st.switch_page("pages/02_Signup.py")

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("Sign In →", use_container_width=True):
        st.switch_page("pages/01_Login.py")

# Stats
st.markdown("""
<div class="stat-row">
    <div class="stat-item"><div class="stat-value">15+</div><div class="stat-label">Sources Searched</div></div>
    <div class="stat-item"><div class="stat-value">3</div><div class="stat-label">AI Prompts Running</div></div>
    <div class="stat-item"><div class="stat-value">100%</div><div class="stat-label">Compliant Sourcing</div></div>
    <div class="stat-item"><div class="stat-value">∞</div><div class="stat-label">Searches Saved</div></div>
</div>
""", unsafe_allow_html=True)

# Sources
st.markdown("""
<div style="text-align:center; color:#475569; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">
    Sources Searched Automatically
</div>
<div class="sources-bar">
    <div class="source-chip">🔵 LinkedIn (X-Ray)</div>
    <div class="source-chip">🐙 GitHub</div>
    <div class="source-chip">📚 Stack Overflow</div>
    <div class="source-chip">📋 Naukri</div>
    <div class="source-chip">📋 Reed</div>
    <div class="source-chip">📋 InfoJobs</div>
    <div class="source-chip">📋 Indeed</div>
    <div class="source-chip">📋 Bayt</div>
    <div class="source-chip">📋 StepStone</div>
    <div class="source-chip">📄 Web CVs</div>
</div>
""", unsafe_allow_html=True)

# Features
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">AI-Powered JD Analysis</div>
        <div class="feature-desc">Paste any job description. Our AI understands hiring intent, infers implicit requirements, and builds a weighted skill matrix — not just keyword matching.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">X-Ray Search</div>
        <div class="feature-desc">Search LinkedIn profiles via Google X-Ray — no LinkedIn subscription needed. Auto-populated Boolean strings built from your JD.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🌍</div>
        <div class="feature-title">Regional Job Boards</div>
        <div class="feature-desc">Automatically searches the right boards for your geography — Naukri for India, Reed for UK, InfoJobs for Spain, Bayt for Middle East.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">AI Match Scoring</div>
        <div class="feature-desc">Every candidate gets a match score against your skill matrix. Know who to prioritize before you read a single profile.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">✉️</div>
        <div class="feature-title">AI Outreach</div>
        <div class="feature-desc">Generate personalised outreach messages for each candidate — LinkedIn, email, or InMail — with one click.</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🤝</div>
        <div class="feature-title">Collaborative Search</div>
        <div class="feature-desc">Not finding the right candidates? Tell the AI what's wrong and it will refine the search. Your pipeline, your team, your results.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center; padding: 3rem 0; color:#334155; font-size:0.78rem;">
    <div style="color:#1E293B; font-size:1rem; font-weight:700; margin-bottom:8px;">
        The<span style="color:#F59E0B;">Sourcer</span>
    </div>
    All sourcing is done via public APIs and Google X-Ray — fully compliant with platform terms of service.
</div>
""", unsafe_allow_html=True)
