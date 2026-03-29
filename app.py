"""
app.py — The Sourcer Landing Page
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.helpers import inject_global_css

st.set_page_config(
    page_title="The Sourcer — AI Talent Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar completely on landing page
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

inject_global_css()

if st.session_state.get("user"):
    st.switch_page("pages/03_Dashboard.py")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.hero-bg {
    position: fixed; inset: 0; z-index: -1;
    background:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(13,148,136,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 85%, rgba(245,158,11,0.10) 0%, transparent 50%),
        #0F172A;
}
.hero-section {
    min-height: 85vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 4rem 1rem 2rem;
}
.tag-pill {
    display: inline-block;
    background: rgba(13,148,136,0.12);
    border: 1px solid rgba(13,148,136,0.35);
    color: #14B8A6;
    border-radius: 999px;
    padding: 5px 16px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: clamp(2.4rem, 5.5vw, 4.2rem);
    font-weight: 800;
    color: #F1F5F9;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 1.25rem;
}
.hero-title .t  { color: #14B8A6; }
.hero-title .g  { color: #F59E0B; }
.hero-sub {
    font-size: 1.05rem;
    color: #64748B;
    max-width: 520px;
    margin: 0 auto 2.5rem;
    line-height: 1.75;
}
.stat-row {
    display: flex; gap: 3rem; justify-content: center;
    flex-wrap: wrap; margin: 2.5rem 0;
}
.stat-item { text-align: center; }
.stat-val { font-size: 2rem; font-weight: 800; color: #14B8A6; }
.stat-lbl {
    font-size: 0.68rem; color: #334155;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin-top: 3px;
}
.sources-row {
    display: flex; gap: 8px; flex-wrap: wrap;
    justify-content: center; margin: 1.5rem 0;
}
.source-chip {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.78rem;
    color: #64748B;
    font-weight: 500;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    max-width: 1080px;
    margin: 3rem auto;
    text-align: left;
}
.feat-card {
    background: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 22px;
    transition: border-color 0.2s;
}
.feat-card:hover { border-color: #0D9488; }
.feat-icon { font-size: 1.6rem; margin-bottom: 10px; }
.feat-title { font-size: 0.92rem; font-weight: 700; color: #F1F5F9; margin-bottom: 6px; }
.feat-desc { font-size: 0.78rem; color: #64748B; line-height: 1.65; }
</style>
<div class="hero-bg"></div>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="tag-pill">🎯 AI-Powered Talent Sourcing</div>
    <div class="hero-title">
        Find the <span class="t">Right Candidates</span><br>
        Before Your <span class="g">Competition Does</span>
    </div>
    <div class="hero-sub">
        The Sourcer searches LinkedIn, GitHub, Stack Overflow, and 15+ job boards
        simultaneously — powered by AI that understands your <em>hiring intent</em>,
        not just keywords.
    </div>
</div>
""", unsafe_allow_html=True)

# ── CTAs ───────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns([2, 1.2, 0.4, 1.2, 2])
with c2:
    if st.button("🚀  Start Sourcing Free", use_container_width=True, type="primary"):
        st.switch_page("pages/02_Signup.py")
with c4:
    if st.button("Sign In →", use_container_width=True):
        st.switch_page("pages/01_Login.py")

# ── Stats ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stat-row">
    <div class="stat-item"><div class="stat-val">15+</div><div class="stat-lbl">Sources Searched</div></div>
    <div class="stat-item"><div class="stat-val">3</div><div class="stat-lbl">AI Prompts</div></div>
    <div class="stat-item"><div class="stat-val">100%</div><div class="stat-lbl">Compliant</div></div>
    <div class="stat-item"><div class="stat-val">∞</div><div class="stat-lbl">Searches Saved</div></div>
</div>
""", unsafe_allow_html=True)

# ── Sources bar ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#1E293B; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:10px;">
    Sources Searched Automatically
</div>
<div class="sources-row">
    <div class="source-chip">🔵 LinkedIn X-Ray</div>
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

# ── Features ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="feature-grid">
    <div class="feat-card">
        <div class="feat-icon">🧠</div>
        <div class="feat-title">AI JD Analysis</div>
        <div class="feat-desc">Paste any job description. AI understands intent, infers implicit requirements, and builds a weighted skill matrix — not just keywords.</div>
    </div>
    <div class="feat-card">
        <div class="feat-icon">🔍</div>
        <div class="feat-title">X-Ray Search</div>
        <div class="feat-desc">Search LinkedIn profiles via Google X-Ray — no LinkedIn subscription needed. Boolean strings built automatically from your JD.</div>
    </div>
    <div class="feat-card">
        <div class="feat-icon">🌍</div>
        <div class="feat-title">Regional Job Boards</div>
        <div class="feat-desc">Automatically searches the right boards for your geography — Naukri (India), Reed (UK), InfoJobs (Spain), Bayt (Middle East).</div>
    </div>
    <div class="feat-card">
        <div class="feat-icon">🎯</div>
        <div class="feat-title">AI Match Scoring</div>
        <div class="feat-desc">Every candidate gets a 0–100 match score against your skill matrix. Know who to prioritise before reading a single profile.</div>
    </div>
    <div class="feat-card">
        <div class="feat-icon">✉️</div>
        <div class="feat-title">AI Outreach</div>
        <div class="feat-desc">Generate personalised LinkedIn and email messages per candidate with one click. Edit and copy — no SMTP needed.</div>
    </div>
    <div class="feat-card">
        <div class="feat-icon">🤝</div>
        <div class="feat-title">Team Collaboration</div>
        <div class="feat-desc">Share candidates with your team. Pipeline stages, notes, and outreach logs synced across everyone in your workspace.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0; border-top:1px solid #1E293B; margin-top:2rem;">
    <div style="font-size:1.1rem; font-weight:800; color:#14B8A6; letter-spacing:-0.02em; margin-bottom:6px;">
        The<span style="color:#F59E0B;">Sourcer</span>
    </div>
    <div style="color:#1E293B; font-size:0.72rem;">
        All sourcing uses public APIs and Google X-Ray search — fully compliant with platform terms.
    </div>
</div>
""", unsafe_allow_html=True)
