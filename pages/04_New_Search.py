import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/04_New_Search.py — New Search
JD input → AI analysis → Filter panel → Source candidates
"""
import streamlit as st
import json
from core.auth import require_auth, load_user_session, get_anthropic_key, get_google_keys, get_github_token
from core.ai_engine import run_full_jd_pipeline, refine_search
from core.sourcing_engine import run_sourcing, get_source_options, get_all_regions
from core.database import save_jd, save_search, update_search_count
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state

st.set_page_config(page_title="New Search — The Sourcer", page_icon="🔍", layout="wide")
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">🔍 New Search</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Paste a job description and let AI build your search — then tweak filters as needed.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Check API keys ─────────────────────────────────────────────────────────────
anthropic_key = get_anthropic_key()
google_keys = get_google_keys()
if not anthropic_key:
    st.error("🔑 **Anthropic API key required.** Go to Settings to add it.")
    if st.button("⚙️ Go to Settings"):
        st.switch_page("pages/09_Settings.py")
    st.stop()

# ── Session state init ────────────────────────────────────────────────────────
if "ai_results" not in st.session_state:
    st.session_state.ai_results = None
if "search_filters" not in st.session_state:
    st.session_state.search_filters = {}
if "sourcing_results" not in st.session_state:
    st.session_state.sourcing_results = None
if "current_jd_text" not in st.session_state:
    st.session_state.current_jd_text = ""
if "search_id" not in st.session_state:
    st.session_state.search_id = None

# Pre-fill from JD library
prefill = st.session_state.pop("prefill_jd", None)
if prefill and not st.session_state.current_jd_text:
    st.session_state.current_jd_text = prefill.get("jd_text", "")
    if prefill.get("ai_analysis"):
        st.session_state.ai_results = {
            "jd_analysis": prefill.get("ai_analysis", {}),
            "skill_matrix": prefill.get("skill_matrix", {}),
        }

# Resume from saved search
resume = st.session_state.pop("resume_search", None)
if resume:
    st.session_state.search_filters = resume.get("filters", {})
    st.session_state.search_id = resume.get("id")
    st.info(f"Resuming search: **{resume.get('name')}**")

# ── STEP 1: JD INPUT ──────────────────────────────────────────────────────────
st.markdown("### Step 1 — Paste Job Description")

jd_text = st.text_area(
    "Job Description",
    value=st.session_state.current_jd_text,
    placeholder="Paste the full job description here. The more detail, the better the AI analysis...",
    height=220,
    label_visibility="collapsed",
)

col_jd1, col_jd2, col_jd3 = st.columns([2, 1, 1])
with col_jd1:
    location_hint = st.text_input(
        "Primary Location (optional)",
        placeholder="e.g. London, India, Remote, New York...",
        value=st.session_state.search_filters.get("location", ""),
    )
with col_jd2:
    search_name = st.text_input(
        "Search Name",
        placeholder="e.g. Senior Python Dev - London",
        value="",
    )
with col_jd3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    save_to_library = st.checkbox("Save JD to Library", value=True)

analyse_col, _, clear_col = st.columns([2, 3, 1])
with analyse_col:
    analyse_btn = st.button("🧠 Analyse JD & Build Search", type="primary", use_container_width=True,
                             disabled=not jd_text.strip())
with clear_col:
    if st.button("Clear", use_container_width=True):
        st.session_state.ai_results = None
        st.session_state.search_filters = {}
        st.session_state.sourcing_results = None
        st.session_state.current_jd_text = ""
        st.rerun()

# ── RUN AI PIPELINE ───────────────────────────────────────────────────────────
if analyse_btn and jd_text.strip():
    st.session_state.current_jd_text = jd_text
    st.session_state.sourcing_results = None

    results = run_full_jd_pipeline(anthropic_key, jd_text, location_hint)

    if results:
        st.session_state.ai_results = results

        # Pre-populate filters from AI
        sp = results.get("search_params", {})
        jda = results.get("jd_analysis", {})

        titles = sp.get("job_titles", {})
        all_titles = titles.get("primary", []) + titles.get("seniority_variants", []) + titles.get("adjacent", [])
        skills_data = sp.get("skills", {})
        all_skills = skills_data.get("core", []) + skills_data.get("supporting", [])

        st.session_state.search_filters = {
            "job_titles": all_titles[:6],
            "skills": all_skills[:10],
            "location": location_hint or sp.get("locations", {}).get("primary", ""),
            "regions": sp.get("regional_job_boards", {}).get("recommended_regions", []),
            "seniority": jda.get("seniority", {}).get("level", "mid"),
            "experience_min": sp.get("filters", {}).get("experience_years_min", 2),
            "experience_max": sp.get("filters", {}).get("experience_years_max", 12),
            "industries": sp.get("companies", {}).get("industries", []),
            "boolean_string": sp.get("boolean_strings", {}).get("primary", ""),
            "boolean_broad": sp.get("boolean_strings", {}).get("broad", ""),
            "boolean_narrow": sp.get("boolean_strings", {}).get("narrow", ""),
        }

        # Save JD to library
        if save_to_library and jd_text.strip():
            jd_title = search_name or jda.get("suggested_job_title", "Untitled JD")
            saved_jd_id = save_jd(
                user_id=user.id,
                title=jd_title,
                jd_text=jd_text,
                ai_analysis=results.get("jd_analysis"),
                skill_matrix=results.get("skill_matrix"),
            )
            st.session_state["current_jd_id"] = saved_jd_id

        st.success("✅ AI analysis complete! Review and adjust the filters below.")
        st.rerun()
    else:
        st.error("AI analysis failed. Please check your API key in Settings.")

# ── STEP 2: AI INSIGHTS (collapsible) ─────────────────────────────────────────
if st.session_state.ai_results:
    ai = st.session_state.ai_results
    jda = ai.get("jd_analysis", {})
    matrix = ai.get("skill_matrix", {})
    sp = ai.get("search_params", {})

    with st.expander("🧠 AI JD Analysis — Click to review", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🎯 Role Intent**")
            st.markdown(jda.get("role_objective", {}).get("problem_solved", "—"))
            st.markdown("**📊 Seniority**")
            st.markdown(f"`{jda.get('seniority', {}).get('level', '—').upper()}`")
            st.markdown("**💡 Ideal Candidate**")
            st.markdown(jda.get("ideal_candidate_brief", "—")[:400])
        with c2:
            st.markdown("**✅ Must-Have Skills**")
            for comp in jda.get("primary_competencies", [])[:5]:
                st.markdown(f"- **{comp.get('name')}** — {comp.get('why_essential', '')[:80]}")
            st.markdown("**⚠️ Disqualifiers**")
            for d in jda.get("evaluation_signals", {}).get("disqualifiers", [])[:3]:
                st.markdown(f"- {d}")

    with st.expander("⚖️ Skill Scoring Matrix", expanded=False):
        skill_items = matrix.get("skill_matrix", [])
        if skill_items:
            import pandas as pd
            df = pd.DataFrame([{
                "Skill": s.get("skill", ""),
                "Category": s.get("category", "").title(),
                "Weight": f"{s.get('weight', 0)}pts",
                "Strong Evidence": s.get("strong_evidence", "")[:80],
            } for s in skill_items])
            st.dataframe(df, use_container_width=True, hide_index=True)
            non_neg = matrix.get("non_negotiables", [])
            if non_neg:
                st.markdown("**🚫 Non-Negotiables (instant reject if missing):**")
                for n in non_neg:
                    st.markdown(f"- {n}")

st.markdown("---")

# ── STEP 3: FILTER PANEL ──────────────────────────────────────────────────────
if st.session_state.ai_results or st.session_state.search_filters:
    st.markdown("### Step 2 — Review & Adjust Search Filters")
    st.markdown('<div style="color:#64748B; font-size:0.82rem; margin-bottom:1rem;">AI has pre-populated these filters. Adjust anything before sourcing.</div>', unsafe_allow_html=True)

    filters = st.session_state.search_filters

    with st.form("filter_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_titles_input = st.text_area(
                "🏷️ Job Titles (one per line)",
                value="\n".join(filters.get("job_titles", [])),
                height=100,
                help="Primary titles + seniority variants + adjacent titles"
            )
            skills_input = st.text_area(
                "🛠️ Skills (one per line)",
                value="\n".join(filters.get("skills", [])),
                height=120,
                help="Core skills the candidate must have"
            )
            location_input = st.text_input(
                "📍 Location",
                value=filters.get("location", ""),
                placeholder="City, Country or Remote"
            )
            all_regions = get_all_regions()
            default_regions = filters.get("regions", [])
            valid_defaults = [r for r in default_regions if r in all_regions]
            regions_input = st.multiselect(
                "🌍 Job Board Regions",
                options=all_regions,
                default=valid_defaults,
                help="Select regions to activate regional job boards"
            )

        with col2:
            seniority_options = ["entry", "mid", "senior", "lead", "head", "principal"]
            current_seniority = filters.get("seniority", "mid")
            if current_seniority not in seniority_options:
                current_seniority = "mid"
            seniority_input = st.selectbox(
                "🎯 Seniority Level",
                options=seniority_options,
                index=seniority_options.index(current_seniority),
            )
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                exp_min = st.number_input("Min Experience (yrs)", min_value=0, max_value=30,
                                          value=int(filters.get("experience_min", 2)))
            with exp_col2:
                exp_max = st.number_input("Max Experience (yrs)", min_value=0, max_value=40,
                                          value=int(filters.get("experience_max", 12)))
            industries_input = st.text_area(
                "🏭 Industries / Company Types",
                value="\n".join(filters.get("industries", [])),
                height=80,
                placeholder="e.g. SaaS, Fintech, Healthcare..."
            )
            boolean_input = st.text_area(
                "🔤 Primary Boolean String",
                value=filters.get("boolean_string", ""),
                height=100,
                help="This is used for LinkedIn X-Ray and job board searches"
            )

        st.markdown("---")
        st.markdown("**📡 Select Sourcing Channels**")
        all_sources = get_source_options()
        source_cols = st.columns(len(all_sources))
        selected_sources = []
        for i, src in enumerate(all_sources):
            with source_cols[i]:
                default_checked = True if src in ["LinkedIn (X-Ray)", "GitHub", "Stack Overflow"] else True
                if st.checkbox(src, value=default_checked, key=f"src_{i}"):
                    selected_sources.append(src)

        st.markdown("---")
        search_name_input = st.text_input(
            "💾 Save this search as",
            value=search_name or st.session_state.ai_results.get("jd_analysis", {}).get("suggested_job_title", "New Search") if st.session_state.ai_results else "New Search",
            placeholder="Give this search a name..."
        )

        max_results = st.slider("Max results per source", min_value=5, max_value=30, value=15, step=5)

        submit_filter = st.form_submit_button("🚀 Source Candidates Now", type="primary", use_container_width=True)

    if submit_filter:
        # Update filters from form
        updated_filters = {
            "job_titles": [t.strip() for t in job_titles_input.strip().split("\n") if t.strip()],
            "skills": [s.strip() for s in skills_input.strip().split("\n") if s.strip()],
            "location": location_input.strip(),
            "regions": regions_input,
            "seniority": seniority_input,
            "experience_min": exp_min,
            "experience_max": exp_max,
            "industries": [i.strip() for i in industries_input.strip().split("\n") if i.strip()],
            "boolean_string": boolean_input.strip(),
        }
        st.session_state.search_filters = updated_filters

        google_api_key = google_keys.get("api_key", "")
        google_cse_id = google_keys.get("cse_id", "")
        github_token = get_github_token()
        skill_matrix = (st.session_state.ai_results or {}).get("skill_matrix", {})
        sp = (st.session_state.ai_results or {}).get("search_params", {})

        if not selected_sources:
            st.warning("Please select at least one sourcing channel.")
            st.stop()

        with st.spinner("⚡ Sourcing candidates across the internet..."):
            candidates = run_sourcing(
                search_params=sp,
                filters=updated_filters,
                selected_sources=selected_sources,
                google_api_key=google_api_key,
                google_cse_id=google_cse_id,
                github_token=github_token,
                anthropic_key=anthropic_key,
                skill_matrix=skill_matrix,
                max_per_source=max_results,
            )

        st.session_state.sourcing_results = candidates

        # Save search record
        jd_id = st.session_state.get("current_jd_id")
        saved_search_id = save_search(
            user_id=user.id,
            name=search_name_input or "Untitled Search",
            jd_id=jd_id,
            filters=updated_filters,
            sources=selected_sources,
            boolean_strings={
                "primary": updated_filters.get("boolean_string", ""),
                "broad": filters.get("boolean_broad", ""),
                "narrow": filters.get("boolean_narrow", ""),
            }
        )
        if saved_search_id:
            update_search_count(saved_search_id, len(candidates))
            st.session_state.search_id = saved_search_id

        if candidates:
            st.success(f"✅ Found **{len(candidates)}** candidates. Scroll down to review results.")
            st.switch_page("pages/05_Search_Results.py")
        else:
            st.warning("No candidates found. Try broadening your Boolean string or adding more regions.")

elif not jd_text.strip():
    st.markdown("---")
    empty_state(
        "📋",
        "Paste a job description above to get started",
        "The AI will analyse the JD and auto-populate all filters for you."
    )
