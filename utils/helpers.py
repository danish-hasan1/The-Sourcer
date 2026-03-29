"""
utils/helpers.py
Shared UI styles, CSS injection, and utility functions for The Sourcer.
"""
import streamlit as st
from typing import Optional


BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Root variables ──────────────────────────────── */
:root {
    --teal:       #0D9488;
    --teal-light: #14B8A6;
    --teal-dark:  #0F766E;
    --amber:      #F59E0B;
    --amber-dark: #D97706;
    --slate-900:  #0F172A;
    --slate-800:  #1E293B;
    --slate-700:  #334155;
    --slate-600:  #475569;
    --slate-400:  #94A3B8;
    --slate-200:  #E2E8F0;
    --slate-100:  #F1F5F9;
    --white:      #FFFFFF;

    --source-linkedin: #0A66C2;
    --source-github:   #6E5494;
    --source-so:       #F48024;
    --source-boards:   #059669;
    --source-web:      #6366F1;
}

/* ── Global resets ──────────────────────────────── */
* { font-family: 'DM Sans', sans-serif !important; }
code, pre { font-family: 'DM Mono', monospace !important; }

.stApp { background: var(--slate-900) !important; }

/* ── Sidebar ────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--slate-800) !important;
    border-right: 1px solid var(--slate-700);
}
[data-testid="stSidebar"] .stMarkdown { color: var(--slate-200) !important; }

/* ── Buttons ────────────────────────────────────── */
.stButton > button {
    background: var(--teal) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--teal-dark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(13,148,136,0.4) !important;
}

/* ── Text inputs ────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--slate-800) !important;
    border: 1px solid var(--slate-700) !important;
    border-radius: 8px !important;
    color: var(--slate-100) !important;
    font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 2px rgba(13,148,136,0.25) !important;
}

/* ── Select/multiselect ─────────────────────────── */
.stSelectbox > div, .stMultiSelect > div {
    background: var(--slate-800) !important;
    border-radius: 8px !important;
}

/* ── Metrics ────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--slate-800) !important;
    border: 1px solid var(--slate-700) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--teal-light) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* ── Expanders ──────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--slate-800) !important;
    border: 1px solid var(--slate-700) !important;
    border-radius: 10px !important;
}

/* ── Tabs ───────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    color: var(--slate-400) !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--teal-light) !important;
    border-bottom-color: var(--teal) !important;
}

/* ── Dividers ───────────────────────────────────── */
hr { border-color: var(--slate-700) !important; opacity: 0.5 !important; }

/* ── Alerts ─────────────────────────────────────── */
.stAlert { border-radius: 10px !important; }

/* ── Page header ─────────────────────────────────── */
.page-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid var(--slate-700);
    margin-bottom: 2rem;
}
.page-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--slate-100);
    margin: 0;
}
.page-subtitle {
    color: var(--slate-400);
    font-size: 0.9rem;
    margin-top: 4px;
}

/* ── Candidate card ──────────────────────────────── */
.candidate-card {
    background: var(--slate-800);
    border: 1px solid var(--slate-700);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s ease;
    position: relative;
}
.candidate-card:hover {
    border-color: var(--teal);
}
.candidate-card .source-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.candidate-card .match-score {
    font-size: 22px;
    font-weight: 700;
    color: var(--teal-light);
}

/* ── Score colors ────────────────────────────────── */
.score-high   { color: #10B981 !important; }
.score-good   { color: var(--teal-light) !important; }
.score-medium { color: var(--amber) !important; }
.score-low    { color: #F87171 !important; }

/* ── Pill badges ─────────────────────────────────── */
.skill-pill {
    display: inline-block;
    background: var(--slate-700);
    color: var(--slate-200);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 11px;
    margin: 2px;
    font-weight: 500;
}

/* ── Logo wordmark ───────────────────────────────── */
.brand-wordmark {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--teal-light);
    letter-spacing: -0.02em;
}
.brand-wordmark span {
    color: var(--amber);
}

/* ── Stage badge ─────────────────────────────────── */
.stage-sourced   { background: #1E3A4A; color: #7DCFFF; }
.stage-reviewed  { background: #2A3A1E; color: #86EFAC; }
.stage-contacted { background: #3A2A1E; color: #FCD34D; }
.stage-responded { background: #1E2A3A; color: #A5B4FC; }
.stage-interview { background: #2A1E3A; color: #F0ABFC; }
.stage-rejected  { background: #3A1E1E; color: #FCA5A5; }

/* ── Progress bar ─────────────────────────────────── */
.stProgress > div > div {
    background: var(--teal) !important;
}
</style>
"""


def inject_global_css():
    """Inject global CSS into every page."""
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a consistent page header."""
    inject_global_css()
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{icon + " " if icon else ""}{title}</div>
        {"<div class='page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def brand_logo(size: str = "md"):
    sizes = {"sm": "1rem", "md": "1.4rem", "lg": "2rem"}
    fs = sizes.get(size, "1.4rem")
    st.markdown(f"""
    <div class="brand-wordmark" style="font-size:{fs}">
        The<span>Sourcer</span>
    </div>
    """, unsafe_allow_html=True)


def score_color_class(score: int) -> str:
    if score >= 80:
        return "score-high"
    elif score >= 65:
        return "score-good"
    elif score >= 45:
        return "score-medium"
    return "score-low"


def score_label(score: int) -> str:
    if score >= 80:
        return "Strong Match"
    elif score >= 65:
        return "Good Match"
    elif score >= 45:
        return "Potential"
    return "Weak Match"


def stage_color(stage: str) -> str:
    colors = {
        "sourced": "#7DCFFF",
        "reviewed": "#86EFAC",
        "contacted": "#FCD34D",
        "responded": "#A5B4FC",
        "interview": "#F0ABFC",
        "rejected": "#FCA5A5",
    }
    return colors.get(stage, "#94A3B8")


def source_icon(source: str) -> str:
    icons = {
        "LinkedIn": "🔵",
        "LinkedIn (X-Ray)": "🔵",
        "GitHub": "🐙",
        "Stack Overflow": "📚",
        "Job Boards": "📋",
        "Web CVs": "📄",
        "Naukri": "📋",
        "Reed": "📋",
        "InfoJobs": "📋",
        "Indeed": "📋",
    }
    for key, icon in icons.items():
        if key.lower() in source.lower():
            return icon
    return "👤"


def format_skills_pills(skills: list, max_show: int = 6) -> str:
    pills = "".join(f'<span class="skill-pill">{s}</span>' for s in skills[:max_show])
    if len(skills) > max_show:
        pills += f'<span class="skill-pill">+{len(skills)-max_show} more</span>'
    return pills


def empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 1rem; color: var(--slate-400, #94A3B8);">
        <div style="font-size:3rem; margin-bottom:1rem;">{icon}</div>
        <div style="font-size:1.1rem; font-weight:600; color: #CBD5E1;">{title}</div>
        {"<div style='font-size:0.85rem; margin-top:0.5rem;'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)
