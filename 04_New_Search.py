import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
pages/04_New_Search.py — New Search
JD → AI analysis → Filter panel → Source candidates
"""
import streamlit as st
import json
from core.auth import require_auth, load_user_session, get_anthropic_key, get_google_keys, get_github_token
from core.ai_engine import run_full_jd_pipeline, refine_search
from core.sourcing_engine import run_sourcing, get_source_options, get_all_regions
from core.database import save_jd, save_search, update_search_count
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css, empty_state

st.set_page_config(
    page_title="New Search — The Sourcer",
    page_icon="🔍",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.25rem 0 0.75rem;">
    <div style="font-size:1.5rem; font-weight:800; color:#F1F5F9;">🔍 New Search</div>
    <div style="color:#64748B; font-size:0.85rem; margin-top:3px;">
        Paste a job description — AI will analyse it and build your search automatically.
    </div>
</div>
""", unsafe_allow_html=True)

# ── API key guard ──────────────────────────────────────────────────────────────
anthropic_key = get_anthropic_key()
if not anthropic_key:
    st.error("🔑 **Anthropic API key required.** Add it in Settings before running searches.")
    if st.button("⚙️ Go to Settings", type="primary"):
        st.switch_page("pages/09_Settings.py")
    st.stop()

google_keys  = get_google_keys()
github_token = get_github_token()

has_google = bool(google_keys.get("api_key") and google_keys.get("cse_id"))
if not has_google:
    st.warning(
        "⚠️ Google Custom Search API keys not set — "
        "LinkedIn X-Ray and Job Board sourcing will be skipped. "
        "Add them in **Settings** for full sourcing capability.",
        icon="🔍",
    )

# ── Session state ──────────────────────────────────────────────────────────────
def _init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_init("ai_results",       None)
_init("search_filters",   {})
_init("sourcing_results", None)
_init("current_jd_text",  "")
_init("search_id",        None)
_init("current_jd_id",    None)

# Pre-fill from JD library
prefill = st.session_state.pop("prefill_jd", None)
if prefill and not st.session_state.current_jd_text:
    st.session_state.current_jd_text = prefill.get("jd_text","")
    if prefill.get("ai_analysis"):
        st.session_state.ai_results = {
            "jd_analysis":  prefill.get("ai_analysis",{}),
            "skill_matrix": prefill.get("skill_matrix",{}),
            "search_params": {},
        }

# Resume saved search
resume = st.session_state.pop("resume_search", None)
if resume:
    st.session_state.search_filters = resume.get("filters",{})
    st.session_state.search_id      = resume.get("id")
    st.info(f"▶ Resuming: **{resume.get('name')}**  — adjust filters below and hit Source.")

# ── STEP 1: JD INPUT ──────────────────────────────────────────────────────────
st.markdown("### 1 · Paste Job Description")

jd_text = st.text_area(
    "Job Description",
    value=st.session_state.current_jd_text,
    placeholder=(
        "Paste the full job description here.\n\n"
        "The more detail you provide, the more accurate the AI analysis will be."
    ),
    height=200,
    label_visibility="collapsed",
)

row1, row2, row3, row4 = st.columns([3, 2, 2, 1])
with row1:
    location_hint = st.text_input(
        "Primary Location",
        placeholder="e.g. London, India, Remote, Dubai…",
        value=st.session_state.search_filters.get("location",""),
    )
with row2:
    search_name = st.text_input(
        "Search Name",
        placeholder="e.g. Senior Python Dev · London",
    )
with row3:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    save_to_library = st.checkbox("💾 Save JD to Library", value=True)
with row4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("🗑 Clear", use_container_width=True):
        for k in ["ai_results","search_filters","sourcing_results","current_jd_text"]:
            st.session_state[k] = None if k == "ai_results" else ({} if k == "search_filters" else ([] if k == "sourcing_results" else ""))
        st.rerun()

analyse_btn = st.button(
    "🧠 Analyse JD & Build Search",
    type="primary",
    use_container_width=False,
    disabled=not jd_text.strip(),
)

# ── RUN AI PIPELINE ───────────────────────────────────────────────────────────
if analyse_btn and jd_text.strip():
    st.session_state.current_jd_text  = jd_text
    st.session_state.sourcing_results = None

    results = run_full_jd_pipeline(anthropic_key, jd_text, location_hint)

    if results:
        st.session_state.ai_results = results
        sp  = results.get("search_params",{})
        jda = results.get("jd_analysis",{})

        titles_data  = sp.get("job_titles",{})
        all_titles   = (titles_data.get("primary",[]) +
                        titles_data.get("seniority_variants",[]) +
                        titles_data.get("adjacent",[]))
        skills_data  = sp.get("skills",{})
        all_skills   = skills_data.get("core",[]) + skills_data.get("supporting",[])

        st.session_state.search_filters = {
            "job_titles":     all_titles[:6],
            "skills":         all_skills[:10],
            "location":       location_hint or sp.get("locations",{}).get("primary",""),
            "regions":        sp.get("regional_job_boards",{}).get("recommended_regions",[]),
            "seniority":      jda.get("seniority",{}).get("level","mid"),
            "experience_min": sp.get("filters",{}).get("experience_years_min",2),
            "experience_max": sp.get("filters",{}).get("experience_years_max",12),
            "industries":     sp.get("companies",{}).get("industries",[]),
            "boolean_string": sp.get("boolean_strings",{}).get("primary",""),
            "boolean_broad":  sp.get("boolean_strings",{}).get("broad",""),
            "boolean_narrow": sp.get("boolean_strings",{}).get("narrow",""),
        }

        if save_to_library and jd_text.strip():
            jd_title   = search_name or jda.get("suggested_job_title","Untitled JD")
            saved_jd_id = save_jd(
                user_id=user.id,
                title=jd_title,
                jd_text=jd_text,
                ai_analysis=results.get("jd_analysis"),
                skill_matrix=results.get("skill_matrix"),
            )
            st.session_state.current_jd_id = saved_jd_id

        st.success("✅ Analysis complete — review filters below and adjust if needed.")
        st.rerun()
    else:
        st.error("AI analysis failed. Please check your Anthropic API key in Settings.")

# ── STEP 2: AI INSIGHTS ────────────────────────────────────────────────────────
if st.session_state.ai_results:
    ai  = st.session_state.ai_results
    jda = ai.get("jd_analysis",{})
    mat = ai.get("skill_matrix",{})

    with st.expander("🧠 AI JD Analysis — click to review", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🎯 Role Intent**")
            st.markdown(jda.get("role_objective",{}).get("problem_solved","—"))
            st.markdown(f"**📊 Seniority:** `{jda.get('seniority',{}).get('level','—').upper()}`")
            st.markdown("**💡 Ideal Candidate**")
            st.markdown((jda.get("ideal_candidate_brief","—") or "—")[:400])
        with c2:
            st.markdown("**✅ Must-Have Skills**")
            for comp in jda.get("primary_competencies",[])[:5]:
                st.markdown(f"- **{comp.get('name')}** — {(comp.get('why_essential',''))[:80]}")
            disc = jda.get("evaluation_signals",{}).get("disqualifiers",[])
            if disc:
                st.markdown("**⛔ Disqualifiers**")
                for d in disc[:3]:
                    st.markdown(f"- {d}")

    with st.expander("⚖️ Skill Scoring Matrix", expanded=False):
        items = mat.get("skill_matrix",[])
        if items:
            import pandas as pd
            df = pd.DataFrame([{
                "Skill":           s.get("skill",""),
                "Category":        s.get("category","").title(),
                "Weight":          f"{s.get('weight',0)} pts",
                "Strong Evidence": (s.get("strong_evidence",""))[:70],
            } for s in items])
            st.dataframe(df, use_container_width=True, hide_index=True)
        nn = mat.get("non_negotiables",[])
        if nn:
            st.markdown("**🚫 Non-Negotiables:**")
            for n in nn:
                st.markdown(f"- {n}")

    st.markdown("---")

    # ── STEP 3: FILTER PANEL ──────────────────────────────────────────────────
    st.markdown("### 2 · Review & Adjust Filters")
    st.markdown(
        '<div style="color:#64748B; font-size:0.82rem; margin-bottom:0.75rem;">'
        'AI pre-populated these — adjust anything before sourcing.</div>',
        unsafe_allow_html=True,
    )

    f = st.session_state.search_filters

    with st.form("filter_form"):
        fc1, fc2 = st.columns(2)

        with fc1:
            titles_val = st.text_area(
                "🏷️ Job Titles (one per line)",
                value="\n".join(f.get("job_titles",[])),
                height=100,
                help="Primary + seniority variants + adjacent titles",
            )
            skills_val = st.text_area(
                "🛠️ Skills (one per line)",
                value="\n".join(f.get("skills",[])),
                height=110,
            )
            location_val = st.text_input(
                "📍 Location",
                value=f.get("location",""),
                placeholder="City, Country or Remote",
            )
            all_regions   = get_all_regions()
            def_regions   = [r for r in f.get("regions",[]) if r in all_regions]
            regions_val   = st.multiselect(
                "🌍 Job Board Regions",
                options=all_regions,
                default=def_regions,
                help="Activates regional job boards for those areas",
            )

        with fc2:
            sen_opts = ["entry","mid","senior","lead","head","principal"]
            cur_sen  = f.get("seniority","mid")
            if cur_sen not in sen_opts:
                cur_sen = "mid"
            seniority_val = st.selectbox(
                "🎯 Seniority Level",
                options=sen_opts,
                index=sen_opts.index(cur_sen),
            )
            ec1, ec2 = st.columns(2)
            with ec1:
                exp_min = st.number_input(
                    "Min Exp (yrs)", min_value=0, max_value=30,
                    value=int(f.get("experience_min",2)),
                )
            with ec2:
                exp_max = st.number_input(
                    "Max Exp (yrs)", min_value=0, max_value=40,
                    value=int(f.get("experience_max",12)),
                )
            industries_val = st.text_area(
                "🏭 Industries",
                value="\n".join(f.get("industries",[])),
                height=80,
                placeholder="e.g. SaaS, Fintech, Healthcare…",
            )
            boolean_val = st.text_area(
                "🔤 Boolean String",
                value=f.get("boolean_string",""),
                height=100,
                help="Used for LinkedIn X-Ray and job board searches",
            )

        st.markdown("---")
        st.markdown("**📡 Sourcing Channels**")
        all_sources = get_source_options()
        s_cols      = st.columns(len(all_sources))
        selected_sources = []
        for si, src in enumerate(all_sources):
            with s_cols[si]:
                if st.checkbox(src, value=True, key=f"src_{si}"):
                    selected_sources.append(src)

        st.markdown("---")
        sn_col, mr_col = st.columns([3, 1])
        with sn_col:
            sn_default = (
                search_name
                or (st.session_state.ai_results or {}).get(
                    "jd_analysis",{}).get("suggested_job_title","New Search")
            )
            search_name_input = st.text_input(
                "💾 Save search as",
                value=sn_default,
                placeholder="Give this search a name…",
            )
        with mr_col:
            max_results = st.slider(
                "Max per source", min_value=5, max_value=30, value=15, step=5,
            )

        source_btn = st.form_submit_button(
            "🚀 Source Candidates Now",
            type="primary",
            use_container_width=True,
        )

    if source_btn:
        updated_filters = {
            "job_titles":     [t.strip() for t in titles_val.strip().split("\n") if t.strip()],
            "skills":         [s.strip() for s in skills_val.strip().split("\n") if s.strip()],
            "location":       location_val.strip(),
            "regions":        regions_val,
            "seniority":      seniority_val,
            "experience_min": exp_min,
            "experience_max": exp_max,
            "industries":     [i.strip() for i in industries_val.strip().split("\n") if i.strip()],
            "boolean_string": boolean_val.strip(),
        }
        st.session_state.search_filters = updated_filters

        if not selected_sources:
            st.warning("Please select at least one sourcing channel.")
            st.stop()

        sp           = (st.session_state.ai_results or {}).get("search_params",{})
        skill_matrix = (st.session_state.ai_results or {}).get("skill_matrix",{})

        with st.spinner("⚡ Sourcing candidates across the internet…"):
            candidates = run_sourcing(
                search_params=sp,
                filters=updated_filters,
                selected_sources=selected_sources,
                google_api_key=google_keys.get("api_key",""),
                google_cse_id=google_keys.get("cse_id",""),
                github_token=github_token,
                anthropic_key=anthropic_key,
                skill_matrix=skill_matrix,
                max_per_source=max_results,
            )

        st.session_state.sourcing_results = candidates

        saved_id = save_search(
            user_id=user.id,
            name=search_name_input or "Untitled Search",
            jd_id=st.session_state.get("current_jd_id"),
            filters=updated_filters,
            sources=selected_sources,
            boolean_strings={
                "primary": updated_filters.get("boolean_string",""),
                "broad":   f.get("boolean_broad",""),
                "narrow":  f.get("boolean_narrow",""),
            },
        )
        if saved_id:
            update_search_count(saved_id, len(candidates))
            st.session_state.search_id = saved_id

        if candidates:
            st.success(f"✅ Found **{len(candidates)}** candidates — loading results…")
            st.switch_page("pages/05_Search_Results.py")
        else:
            st.warning(
                "No candidates found. Try:\n"
                "- Broadening your Boolean string\n"
                "- Adding more regions\n"
                "- Checking your Google API key in Settings"
            )

elif not jd_text.strip():
    st.markdown("---")
    empty_state(
        "📋",
        "Paste a job description above to get started",
        "AI will analyse the JD and auto-populate all filters for you.",
    )
