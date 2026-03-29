"""
pages/search.py — Candidate search page for the Streamlit app.

Two modes:
  1. JD-driven  — paste/fetch a JD, run the 3-prompt chain, review/edit
                  auto-populated filters, then search.
  2. Manual     — fill in filters directly, search immediately.

Both modes validate required fields before allowing search to fire.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from jd_analysis   import run_chain, validate_jd
from boolean_builder import generate_all_strings, validate_filters
from db            import (init_db, create_job, update_job_chain_outputs,
                           update_job_filters, get_job_candidates, list_jobs)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Candidate Search", layout="wide")
init_db()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
def _init_state():
    defaults = {
        "mode":           "jd",          # "jd" | "manual"
        "jd_text":        "",
        "chain_done":     False,
        "chain_error":    None,
        "p1_out":         {},
        "p2_out":         {},
        "p3_out":         {},
        "filter_config":  {},
        "job_id":         None,
        "search_done":    False,
        "results":        [],
        # Editable filter fields (populated by chain or entered manually)
        "f_titles":       "",
        "f_must_skills":  [],
        "f_nice_skills":  [],
        "f_exp_range":    "",
        "f_seniority":    "",
        "f_location":     "",
        "f_industry":     "",
        "f_exclude":      [],
        "f_sources":      {
            "linkedin": True,
            "github":   True,
            "naukri":   True,
            "google":   True,
            "db_only":  False,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_search():
    """Clear search results when filters change."""
    st.session_state.search_done = False
    st.session_state.results = []


def _populate_filters_from_chain():
    """Copy chain output into editable session state filter fields."""
    fc = st.session_state.filter_config
    st.session_state.f_titles      = ", ".join(fc.get("titles", []))
    st.session_state.f_must_skills = fc.get("must_skills", [])
    st.session_state.f_nice_skills = fc.get("nice_skills", [])
    st.session_state.f_exp_range   = fc.get("exp_range", "")
    st.session_state.f_seniority   = fc.get("seniority", "")
    st.session_state.f_location    = fc.get("location", "")
    st.session_state.f_industry    = fc.get("industry", "")
    st.session_state.f_exclude     = fc.get("exclude", [])


def _current_filter_config() -> dict:
    """Build a filter config dict from current session state fields."""
    titles = [t.strip() for t in st.session_state.f_titles.split(",") if t.strip()]
    return {
        "titles":      titles,
        "must_skills": st.session_state.f_must_skills,
        "nice_skills": st.session_state.f_nice_skills,
        "exp_range":   st.session_state.f_exp_range,
        "seniority":   st.session_state.f_seniority,
        "location":    st.session_state.f_location,
        "industry":    st.session_state.f_industry,
        "exclude":     st.session_state.f_exclude,
        "sources":     st.session_state.f_sources,
    }


# ---------------------------------------------------------------------------
# Mode toggle
# ---------------------------------------------------------------------------

st.title("Candidate search")

col_jd, col_manual = st.columns(2)
with col_jd:
    if st.button("JD-driven search",
                 type="primary" if st.session_state.mode == "jd" else "secondary",
                 use_container_width=True):
        st.session_state.mode = "jd"
        _reset_search()

with col_manual:
    if st.button("Manual search",
                 type="primary" if st.session_state.mode == "manual" else "secondary",
                 use_container_width=True):
        st.session_state.mode = "manual"
        _reset_search()

st.divider()


# ===========================================================================
# MODE 1 — JD-DRIVEN
# ===========================================================================

if st.session_state.mode == "jd":

    # -----------------------------------------------------------------------
    # Step 1 — JD input
    # -----------------------------------------------------------------------
    with st.expander("Step 1 — Job description", expanded=not st.session_state.chain_done):

        jd_tab1, jd_tab2 = st.tabs(["Paste JD", "Fetch from URL"])

        with jd_tab1:
            st.session_state.jd_text = st.text_area(
                "Paste the full job description",
                value=st.session_state.jd_text,
                height=240,
                placeholder="Paste the complete job description here...",
                label_visibility="collapsed",
            )

        with jd_tab2:
            jd_url = st.text_input("Job posting URL",
                                   placeholder="https://company.com/careers/job-id")
            if st.button("Fetch JD from URL") and jd_url:
                with st.spinner("Fetching job description..."):
                    try:
                        # Playwright fetch — reuse your existing scraper
                        from scraper import fetch_jd_text  # type: ignore
                        st.session_state.jd_text = fetch_jd_text(jd_url)
                        st.success("JD fetched successfully.")
                    except ImportError:
                        st.warning("scraper.py not found — paste the JD manually for now.")
                    except Exception as e:
                        st.error(f"Fetch failed: {e}")

        # Validation warnings
        if st.session_state.jd_text:
            warnings = validate_jd(st.session_state.jd_text)
            for w in warnings:
                st.warning(w)

    # -----------------------------------------------------------------------
    # Step 2 — Run the 3-prompt chain
    # -----------------------------------------------------------------------
    with st.expander("Step 2 — Analyse with AI",
                     expanded=bool(st.session_state.jd_text) and not st.session_state.chain_done):

        # Progress display (only shown after run starts)
        if st.session_state.chain_done:
            st.success("Analysis complete — filters populated in Step 3.")
        elif st.session_state.chain_error:
            st.error(st.session_state.chain_error)

        can_run = bool(st.session_state.jd_text and
                       len(st.session_state.jd_text.strip()) > 80)

        if not can_run:
            st.info("Paste a job description above to enable analysis.")

        if st.button("Run analysis chain (3 prompts)",
                     disabled=not can_run,
                     type="primary"):

            st.session_state.chain_done  = False
            st.session_state.chain_error = None
            _reset_search()

            progress_bar  = st.progress(0)
            status_text   = st.empty()

            step_labels = {
                1: "Prompt 1 — JD dissection & intent extraction...",
                2: "Prompt 2 — Weighted skill & competency matrix...",
                3: "Prompt 3 — Sourcing parameters & boolean builder...",
            }

            def on_step(step: int, label: str):
                progress_bar.progress(step / 3)
                status_text.write(f"✓ {label}")

            with st.spinner("Running analysis — this takes ~15 seconds..."):
                result = run_chain(
                    st.session_state.jd_text,
                    on_step=on_step,
                )

            if result["error"]:
                st.session_state.chain_error = result["error"]
                st.error(result["error"])
            else:
                st.session_state.p1_out        = result["p1"]
                st.session_state.p2_out        = result["p2"]
                st.session_state.p3_out        = result["p3"]
                st.session_state.filter_config = result["filter_config"]
                st.session_state.chain_done    = True
                _populate_filters_from_chain()

                # Save to DB
                job_title = (result["p1"].get("role_objective") or
                             result["filter_config"].get("titles", ["New job"])[0] or
                             "New job")
                job_id = create_job(
                    title=job_title,
                    jd_text=st.session_state.jd_text,
                )
                update_job_chain_outputs(
                    job_id,
                    p1=result["p1_raw"],
                    p2=result["p2_raw"],
                    p3=result["p3_raw"],
                )
                st.session_state.job_id = job_id
                progress_bar.progress(1.0)
                status_text.write("✓ All 3 prompts complete")
                st.rerun()

        # Show raw outputs in expanders for transparency
        if st.session_state.chain_done:
            with st.expander("View Prompt 1 output — role analysis"):
                st.json(st.session_state.p1_out)
            with st.expander("View Prompt 2 output — skills matrix"):
                st.json(st.session_state.p2_out)
            with st.expander("View Prompt 3 output — sourcing params"):
                st.json(st.session_state.p3_out)


# ===========================================================================
# FILTER PANEL — shared by both modes (JD-driven auto-populates, manual = blank)
# ===========================================================================

st.subheader("Search filters")

if st.session_state.mode == "jd" and st.session_state.chain_done:
    st.caption("AI-populated from your JD — edit freely before searching.")
elif st.session_state.mode == "jd":
    st.caption("Run the analysis chain above to auto-populate these filters.")

# ---- Required fields ------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.session_state.f_titles = st.text_input(
        "Job titles *(required)*",
        value=st.session_state.f_titles,
        placeholder="RPO Delivery Manager, Head of Talent, TA Lead",
        on_change=_reset_search,
    )

with col2:
    st.session_state.f_exp_range = st.text_input(
        "Experience range *(required)*",
        value=st.session_state.f_exp_range,
        placeholder="e.g. 8–14 years",
        on_change=_reset_search,
    )

st.session_state.f_location = st.text_input(
    "Location *(required)*",
    value=st.session_state.f_location,
    placeholder="e.g. Bangalore, Hyderabad, remote India",
    on_change=_reset_search,
)

# ---- Skills ---------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    # Must-have skills as editable multiselect
    current_must = st.session_state.f_must_skills or []
    new_must = st.multiselect(
        "Must-have skills",
        options=current_must,
        default=current_must,
    )
    # Allow free-text addition
    new_must_skill = st.text_input("Add must-have skill", key="add_must",
                                    placeholder="Type skill and press Enter")
    if new_must_skill and new_must_skill not in st.session_state.f_must_skills:
        st.session_state.f_must_skills.append(new_must_skill)
        _reset_search()
        st.rerun()
    st.session_state.f_must_skills = new_must

with col4:
    current_nice = st.session_state.f_nice_skills or []
    new_nice = st.multiselect(
        "Nice-to-have skills",
        options=current_nice,
        default=current_nice,
    )
    new_nice_skill = st.text_input("Add nice-to-have skill", key="add_nice",
                                    placeholder="Type skill and press Enter")
    if new_nice_skill and new_nice_skill not in st.session_state.f_nice_skills:
        st.session_state.f_nice_skills.append(new_nice_skill)
        _reset_search()
        st.rerun()
    st.session_state.f_nice_skills = new_nice

# ---- Optional fields ------------------------------------------------------
col5, col6 = st.columns(2)

with col5:
    seniority_options = ["", "Junior", "Mid-level", "Senior", "Lead", "Head / Principal"]
    cur_sen = st.session_state.f_seniority
    sen_idx = seniority_options.index(cur_sen) if cur_sen in seniority_options else 0
    st.session_state.f_seniority = st.selectbox(
        "Seniority", seniority_options, index=sen_idx, on_change=_reset_search
    )

with col6:
    st.session_state.f_industry = st.text_input(
        "Industry / background",
        value=st.session_state.f_industry,
        placeholder="e.g. RPO, MSP, In-house TA",
        on_change=_reset_search,
    )

# ---- Exclusions -----------------------------------------------------------
current_excl = st.session_state.f_exclude or []
new_excl = st.multiselect(
    "Exclude terms",
    options=current_excl,
    default=current_excl,
)
new_excl_term = st.text_input("Add exclusion term", key="add_excl",
                               placeholder="e.g. agency recruiter, trainee")
if new_excl_term and new_excl_term not in st.session_state.f_exclude:
    st.session_state.f_exclude.append(new_excl_term)
    _reset_search()
    st.rerun()
st.session_state.f_exclude = new_excl

# ---- Sources --------------------------------------------------------------
st.markdown("**Search sources**")
src_cols = st.columns(5)
source_labels = {
    "linkedin": "LinkedIn",
    "github":   "GitHub",
    "naukri":   "Naukri / Indeed",
    "google":   "Google X-ray",
    "db_only":  "Existing DB only",
}
for i, (k, label) in enumerate(source_labels.items()):
    with src_cols[i]:
        st.session_state.f_sources[k] = st.checkbox(
            label,
            value=st.session_state.f_sources[k],
            key=f"src_{k}",
        )

# ---- Boolean preview ------------------------------------------------------
fc = _current_filter_config()
if fc.get("titles") or fc.get("must_skills"):
    boolean_strings = generate_all_strings(fc)
    with st.expander("Boolean search strings (auto-generated)"):
        st.markdown("**Balanced (default)**")
        st.code(boolean_strings["linkedin_balanced"], language="text")
        st.markdown("**Broad** — maximum discovery")
        st.code(boolean_strings["linkedin_broad"], language="text")
        st.markdown("**Narrow** — high precision")
        st.code(boolean_strings["linkedin_narrow"], language="text")
        st.markdown("**GitHub X-ray**")
        st.code(boolean_strings["github"], language="text")

# ---- Non-negotiables warning (from Prompt 2) ------------------------------
non_neg = st.session_state.filter_config.get("non_negotiables", [])
if non_neg:
    with st.expander(f"Non-negotiable conditions ({len(non_neg)}) — candidates missing these should be rejected"):
        for nn in non_neg:
            st.markdown(f"- {nn}")

st.divider()

# ---- SEARCH BUTTON --------------------------------------------------------
missing_fields = validate_filters(fc)

if missing_fields:
    for m in missing_fields:
        st.warning(f"Required: {m}")

search_clicked = st.button(
    "Search candidates",
    type="primary",
    disabled=bool(missing_fields),
    use_container_width=True,
)

if search_clicked and not missing_fields:
    # Save filter config to DB if we have a job_id
    if st.session_state.job_id:
        boolean_strings = generate_all_strings(fc)
        update_job_filters(
            st.session_state.job_id,
            filter_config=fc,
            boolean_string=boolean_strings["linkedin_balanced"],
        )

    st.session_state.search_done = True
    # TODO: trigger actual scraper here and populate st.session_state.results
    st.info("Search triggered — scrapers will populate results here. "
            "Wire in your Playwright scrapers to this point.")


# ===========================================================================
# RESULTS
# ===========================================================================

if st.session_state.search_done:
    st.subheader("Results")

    tab_ranked, tab_bool, tab_pipeline = st.tabs(
        ["Ranked matches", "Boolean / raw results", "Pipeline"]
    )

    with tab_ranked:
        results = st.session_state.results
        if not results:
            st.info("No results yet — scraper results will appear here once sourcing completes.")
        else:
            for c in results:
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.markdown(f"**{c.get('full_name', 'Unknown')}**")
                        st.caption(f"{c.get('current_title','')} @ {c.get('current_company','')}")
                        skills = c.get("skills", [])
                        if skills:
                            st.caption("Skills: " + " · ".join(skills[:6]))
                    with col_b:
                        score = c.get("match_score", 0)
                        color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                        st.markdown(f":{color}[**{score:.0f}/100**]")
                    with col_c:
                        stage = st.selectbox(
                            "Stage",
                            ["found", "shortlisted", "contacted", "responded", "rejected"],
                            key=f"stage_{c.get('id')}",
                        )

    with tab_bool:
        if fc.get("titles") or fc.get("must_skills"):
            boolean_strings = generate_all_strings(fc)
            st.markdown("Copy these into Google or LinkedIn search:")
            st.code(boolean_strings["linkedin_balanced"], language="text")
            st.code(boolean_strings["linkedin_broad"],    language="text")
            st.code(boolean_strings["linkedin_narrow"],   language="text")
        else:
            st.info("Fill in filters above to generate boolean strings.")

    with tab_pipeline:
        if st.session_state.job_id:
            pipeline_candidates = get_job_candidates(st.session_state.job_id)
            stages = ["found", "shortlisted", "contacted", "responded", "rejected"]
            stage_cols = st.columns(len(stages))
            for i, stage in enumerate(stages):
                with stage_cols[i]:
                    in_stage = [c for c in pipeline_candidates if c.get("stage") == stage]
                    st.markdown(f"**{stage.title()}** ({len(in_stage)})")
                    for c in in_stage:
                        st.caption(c.get("full_name", "Unknown"))
        else:
            st.info("Pipeline tracking will appear here once a job is saved.")
