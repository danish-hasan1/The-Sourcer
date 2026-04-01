"""
pages/11_Boolean_Builder.py — Boolean String Builder Tool
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.auth import require_auth, load_user_session, get_anthropic_key
from components.sidebar import render_sidebar
from utils.helpers import inject_global_css
import anthropic
import json

st.set_page_config(
    page_title="Boolean Builder — The Sourcer",
    page_icon="🔤",
    layout="wide",
)
inject_global_css()
require_auth()

user = st.session_state.user
load_user_session(user.id)
render_sidebar()

st.markdown("""
<div style="padding:1.5rem 0 1rem;">
    <div style="font-size:1.6rem; font-weight:800; color:#F1F5F9;">🔤 Boolean String Builder</div>
    <div style="color:#64748B; font-size:0.88rem; margin-top:4px;">
        Build, test, and refine Boolean search strings for any platform.
    </div>
</div>
""", unsafe_allow_html=True)

anthropic_key = get_anthropic_key()

tab1, tab2, tab3 = st.tabs(["🤖 AI Builder", "🛠️ Manual Builder", "📚 Reference Guide"])

# ── AI BUILDER ────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Build Boolean String from Job Description")
    st.markdown('<div style="color:#64748B; font-size:0.85rem; margin-bottom:1rem;">Paste a JD or describe the role — AI will generate optimised Boolean strings for each platform.</div>', unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        jd_input = st.text_area(
            "Job Description or Role Description",
            placeholder="e.g. We're looking for a Senior Python Engineer with 5+ years experience in Django, AWS, and microservices architecture. Experience with Kafka is a plus.",
            height=200,
            label_visibility="collapsed",
        )
        platform = st.selectbox(
            "Target Platform",
            ["LinkedIn (X-Ray via Google)", "GitHub", "Stack Overflow", "Naukri (India)", "Reed (UK)", "InfoJobs (Spain)", "Indeed", "All Platforms"],
        )
        style = st.radio(
            "Search Style",
            ["Balanced (Precision + Reach)", "Broad (Maximum Discovery)", "Narrow (High Precision)"],
            horizontal=True,
        )

        if not anthropic_key:
            st.warning("⚠️ Add your Anthropic API key in Settings to use AI Builder.")

        generate_btn = st.button(
            "⚡ Generate Boolean Strings",
            type="primary",
            use_container_width=True,
            disabled=not jd_input.strip() or not anthropic_key,
        )

    with col_out:
        if "bool_results" not in st.session_state:
            st.session_state.bool_results = None

        if generate_btn and jd_input.strip() and anthropic_key:
            style_map = {
                "Balanced (Precision + Reach)": "balanced",
                "Broad (Maximum Discovery)": "broad",
                "Narrow (High Precision)": "narrow",
            }

            _SYSTEM = """You are a senior sourcing recruiter and Boolean search expert.
Generate optimised Boolean search strings for candidate sourcing.
Return ONLY valid JSON, no markdown, no explanation:
{
  "role_understood": "string",
  "key_terms": ["string"],
  "strings": {
    "linkedin_xray": "string",
    "github": "string",
    "stackoverflow": "string",
    "naukri": "string",
    "reed": "string",
    "infojobs": "string",
    "indeed": "string",
    "generic": "string"
  },
  "title_variations": ["string"],
  "skill_synonyms": {"skill": ["synonym1", "synonym2"]},
  "tips": ["string"]
}"""

            prompt = f"""Role/JD: {jd_input}
Platform focus: {platform}
Style: {style_map.get(style, 'balanced')}

Generate Boolean search strings. For X-Ray searches, use site: operator format.
For LinkedIn X-Ray: site:linkedin.com/in/ format.
Include OR groups for synonyms, AND for required terms, NOT for exclusions."""

            with st.spinner("🤖 Building Boolean strings..."):
                try:
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    msg = client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=2000,
                        system=_SYSTEM,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    raw = msg.content[0].text.strip().strip("```json").strip("```").strip()
                    st.session_state.bool_results = json.loads(raw)
                except json.JSONDecodeError:
                    st.session_state.bool_results = {"strings": {"generic": msg.content[0].text}}
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.bool_results:
            res = st.session_state.bool_results

            if res.get("role_understood"):
                st.markdown(f"""
                <div style="background:#1E293B; border-left:3px solid #0D9488; border-radius:0 8px 8px 0; padding:10px 14px; margin-bottom:1rem; font-size:0.85rem; color:#94A3B8;">
                    <b style="color:#14B8A6;">Role understood:</b> {res['role_understood']}
                </div>
                """, unsafe_allow_html=True)

            strings = res.get("strings", {})
            platform_labels = {
                "linkedin_xray": "🔵 LinkedIn X-Ray (Google)",
                "github": "🐙 GitHub",
                "stackoverflow": "📚 Stack Overflow",
                "naukri": "📋 Naukri (India)",
                "reed": "📋 Reed (UK)",
                "infojobs": "📋 InfoJobs (Spain)",
                "indeed": "📋 Indeed",
                "generic": "🔍 Generic Boolean",
            }

            for key, label in platform_labels.items():
                val = strings.get(key, "")
                if val and val != "N/A":
                    st.markdown(f"**{label}**")
                    st.code(val, language=None)

            if res.get("title_variations"):
                st.markdown("**📌 Title Variations to Try:**")
                st.markdown(" · ".join(f"`{t}`" for t in res["title_variations"]))

            if res.get("tips"):
                st.markdown("**💡 Sourcing Tips:**")
                for tip in res["tips"]:
                    st.markdown(f"- {tip}")

            # Use in search button
            generic_str = strings.get("linkedin_xray") or strings.get("generic", "")
            if generic_str and st.button("🔍 Use This in New Search", type="primary"):
                st.session_state.search_filters = st.session_state.get("search_filters", {})
                st.session_state.search_filters["boolean_string"] = generic_str
                st.switch_page("pages/04_New_Search.py")
        else:
            st.markdown("""
            <div style="background:#1E293B; border:1px dashed #334155; border-radius:12px; padding:3rem 2rem; text-align:center;">
                <div style="font-size:2rem; margin-bottom:1rem;">🔤</div>
                <div style="color:#64748B; font-size:0.88rem;">Boolean strings will appear here</div>
            </div>
            """, unsafe_allow_html=True)

# ── MANUAL BUILDER ────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Manual Boolean Builder")
    st.markdown('<div style="color:#64748B; font-size:0.85rem; margin-bottom:1.5rem;">Build a Boolean string step by step. The string auto-updates as you fill in fields.</div>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)

    with m1:
        required_terms = st.text_area(
            "Required terms (AND)",
            placeholder="python\ndjango\naws",
            height=100,
            help="All these terms must appear. One per line.",
        )
        any_of_terms = st.text_area(
            "Any of these (OR groups)",
            placeholder="senior, lead, principal\ndeveloper, engineer, architect",
            height=100,
            help="Each line is an OR group. Separate synonyms with comma.",
        )
        exclude_terms = st.text_area(
            "Exclude (NOT)",
            placeholder="recruiter\njunior\ninternship",
            height=80,
            help="Terms to exclude. One per line.",
        )

    with m2:
        job_titles = st.text_area(
            "Job titles to include",
            placeholder='\"software engineer\"\n\"backend developer\"\n\"python developer\"',
            height=100,
            help="Wrap multi-word titles in quotes. One per line.",
        )
        location_bool = st.text_input(
            "Location filter",
            placeholder='e.g. London OR "United Kingdom"',
        )
        site_target = st.selectbox(
            "Prepend site: filter",
            ["None", "site:linkedin.com/in/", "site:naukri.com", "site:reed.co.uk",
             "site:infojobs.net", "site:github.com", "site:stackoverflow.com"],
        )

    # Build the Boolean string
    parts = []

    # Site prefix
    if site_target != "None":
        parts.append(site_target)

    # Location
    if location_bool.strip():
        parts.append(f"({location_bool.strip()})")

    # Titles
    title_lines = [t.strip() for t in job_titles.strip().split("\n") if t.strip()]
    if title_lines:
        parts.append(f"({' OR '.join(title_lines)})")

    # Required terms
    req_lines = [t.strip() for t in required_terms.strip().split("\n") if t.strip()]
    for req in req_lines:
        parts.append(req)

    # OR groups
    or_lines = [l.strip() for l in any_of_terms.strip().split("\n") if l.strip()]
    for line in or_lines:
        synonyms = [s.strip() for s in line.split(",") if s.strip()]
        if len(synonyms) > 1:
            parts.append(f"({' OR '.join(synonyms)})")
        elif synonyms:
            parts.append(synonyms[0])

    # Exclusions
    exc_lines = [t.strip() for t in exclude_terms.strip().split("\n") if t.strip()]
    for exc in exc_lines:
        parts.append(f"-{exc}")

    final_bool = " ".join(parts)

    st.markdown("---")
    st.markdown("**🔤 Your Boolean String:**")
    if final_bool.strip():
        st.code(final_bool, language=None)
        char_count = len(final_bool)
        color = "#10B981" if char_count < 500 else "#F59E0B" if char_count < 1000 else "#F87171"
        st.markdown(f'<div style="font-size:0.75rem; color:{color};">{char_count} characters</div>', unsafe_allow_html=True)

        if st.button("🔍 Use in New Search", type="primary", key="manual_use"):
            st.session_state.search_filters = st.session_state.get("search_filters", {})
            st.session_state.search_filters["boolean_string"] = final_bool
            st.switch_page("pages/04_New_Search.py")
    else:
        st.markdown('<div style="color:#475569; font-size:0.85rem;">Fill in the fields above to generate your Boolean string.</div>', unsafe_allow_html=True)

# ── REFERENCE GUIDE ────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 📚 Boolean Search Reference Guide")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
#### Core Operators

| Operator | Meaning | Example |
|---|---|---|
| `AND` | Both must appear | `python AND django` |
| `OR` | Either can appear | `developer OR engineer` |
| `NOT` or `-` | Must not appear | `NOT recruiter` or `-recruiter` |
| `"..."` | Exact phrase | `"software engineer"` |
| `(...)` | Group terms | `(python OR java)` |
| `*` | Wildcard | `develop*` |

#### X-Ray Search Format (Google)
```
site:linkedin.com/in/ "London" (python OR django) 
("software engineer" OR "backend developer") 
-recruiter -intern
```

#### GitHub Search
```
location:london language:python followers:>50
```

#### Stack Overflow
```
[python] [django] answers:>10 location:london
```
        """)

    with col_b:
        st.markdown("""
#### Platform Quick Reference

**LinkedIn X-Ray (via Google)**
- `site:linkedin.com/in/` prefix
- Use `"quoted titles"` for exact match
- Location in quotes: `"New York"`

**Naukri (India)**
- `site:naukri.com` prefix  
- `resume` or `profile` as keyword
- Example: `site:naukri.com python developer Bangalore resume`

**Reed (UK)**
- `site:reed.co.uk` prefix
- Example: `site:reed.co.uk "product manager" London`

**InfoJobs (Spain)**
- `site:infojobs.net` prefix
- Mix Spanish/English: `desarrollador OR developer`

#### Seniority Strings
```
(senior OR lead OR principal OR staff OR "tech lead")
(junior OR associate OR graduate OR entry)  
(head OR director OR VP OR "vice president")
```

#### Common Exclusions
```
-recruiter -"talent acquisition" -HR -staffing 
-intern -internship -freelance -contractor
```
        """)

    st.markdown("---")
    st.markdown("""
#### 💡 Pro Tips

- **Start broad, then narrow** — begin with OR groups, add AND constraints if too many results
- **Test your string** — paste it into Google and review the first 10 results
- **Synonym first** — for rare roles, cast wide with many OR synonyms before adding AND requirements  
- **Location variants** — `"United Kingdom" OR "UK" OR England OR London` catches more profiles
- **Exclude noise** — `-recruiter -"looking for" -hiring` removes job posts from results
    """)
