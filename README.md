# 🎯 The Sourcer — AI Talent Intelligence Platform

> Find the right candidates before your competition does.

The Sourcer is an AI-powered talent sourcing platform that searches LinkedIn (via X-Ray), GitHub, Stack Overflow, and 15+ regional job boards simultaneously — powered by Claude AI that understands your *hiring intent*, not just keywords.

---

## ✨ Features

- **🧠 AI JD Analysis** — 3-stage intelligence pipeline: intent extraction → skill matrix → search parameters
- **🔍 X-Ray Sourcing** — LinkedIn profiles via Google Custom Search (legal, compliant)
- **🐙 GitHub Search** — Developer profiles via official GitHub API
- **📚 Stack Overflow** — Expert developers via Stack Exchange API
- **🌍 Regional Job Boards** — Naukri (India), Reed (UK), InfoJobs (Spain), Bayt (Middle East), StepStone (Germany), Indeed, Monster, and more
- **📄 Web CVs** — Public CV documents across the open web
- **🎯 AI Match Scoring** — Every candidate scored 0-100 against your skill matrix
- **✉️ AI Outreach** — Personalised LinkedIn and email messages generated in one click
- **📊 Pipeline Kanban** — Track candidates from Sourced → Interview
- **🤝 Team Sharing** — Collaborate with colleagues on the same candidate pool
- **💾 Saved Searches** — Resume, clone, and reuse past searches
- **📄 JD Library** — Save and reuse job descriptions
- **🛡️ Admin Panel** — User management and platform analytics
- **🎓 Onboarding Tutorial** — Guided first-time setup

---

## 🚀 Setup Guide

### Step 1 — Clone the Repository

```bash
git clone https://github.com/yourusername/the-sourcer.git
cd the-sourcer
pip install -r requirements.txt
```

### Step 2 — Set Up Supabase

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **New Project** — give it a name (e.g. "the-sourcer")
3. Set a strong database password (save it somewhere)
4. Wait ~2 minutes for the project to initialise
5. Go to **SQL Editor** (left sidebar)
6. Click **New Query**
7. Copy the entire contents of `supabase_schema.sql` and paste it
8. Click **Run** — you should see "Success"
9. Go to **Settings → API**
10. Copy your **Project URL** and **anon public** key

### Step 3 — Configure Secrets

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
```

### Step 4 — Run Locally

```bash
streamlit run app.py
```

### Step 5 — Create Your Admin Account

1. Open the app at `http://localhost:8501`
2. Click **Create Account** and sign up
3. Go to your Supabase dashboard → **Table Editor** → `profiles`
4. Find your row and change `role` from `user` to `admin`
5. Refresh the app — you now have the Admin Panel

---

## 🔑 API Keys (Set in Settings after login)

### Required — Anthropic API Key
- Go to [console.anthropic.com](https://console.anthropic.com)
- **API Keys** → **Create Key**

### Required — Google Custom Search (for X-Ray)
**Step A — Google API Key:**
1. [console.cloud.google.com](https://console.cloud.google.com) → Create project
2. **APIs & Services** → **Credentials** → **Create Credentials** → **API Key**

**Step B — Enable Custom Search API:**
1. **APIs & Services** → **Library** → Search "Custom Search API" → Enable

**Step C — Search Engine ID:**
1. [programmablesearchengine.google.com](https://programmablesearchengine.google.com)
2. Create engine → **Search the entire web** → Copy **Search Engine ID**

*Free tier: 100 searches/day*

### Optional — GitHub Token (increases rate limits)
- github.com → **Settings** → **Developer settings** → **Personal access tokens** → Generate
- Scopes needed: `read:user`, `user:email`

---

## ☁️ Deploy to Streamlit Cloud

1. Push your code to a **private** GitHub repo (never push secrets.toml!)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → Connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Advanced settings** → **Secrets** and paste:
```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
```
6. Click **Deploy**

---

## 📁 Project Structure

```
the-sourcer/
├── app.py                          # Landing page
├── requirements.txt
├── supabase_schema.sql             # Database setup (run once)
├── .streamlit/
│   ├── config.toml                 # Theme settings
│   └── secrets.toml.template       # Secrets template
├── pages/
│   ├── 01_Login.py
│   ├── 02_Signup.py
│   ├── 03_Dashboard.py
│   ├── 04_New_Search.py            # Core: JD → AI → Filters → Source
│   ├── 05_Search_Results.py        # Candidate cards + save + outreach
│   ├── 06_Candidate_Database.py    # Pipeline + list + table views
│   ├── 07_Saved_Searches.py        # Search history + JD library
│   ├── 08_Outreach.py              # AI message generation
│   ├── 09_Settings.py              # API keys + profile + team
│   └── 10_Admin.py                 # Admin panel
├── core/
│   ├── auth.py                     # Authentication
│   ├── database.py                 # All DB operations
│   ├── ai_engine.py                # AI prompts (hidden)
│   ├── sourcing_engine.py          # Search orchestrator
│   └── sources/
│       ├── google_xray.py          # X-Ray + job boards
│       ├── github_source.py        # GitHub API
│       └── stackoverflow_source.py # Stack Exchange API
├── components/
│   ├── sidebar.py                  # Navigation
│   ├── onboarding.py               # Tutorial
│   └── candidate_card.py          # Profile card
└── utils/
    ├── deduplication.py
    └── helpers.py                  # CSS + UI utilities
```

---

## ⚖️ Compliance Notes

All sourcing methods used by The Sourcer are fully compliant:

- **LinkedIn X-Ray** uses Google Custom Search (`site:linkedin.com/in/`) — this is standard Google search, no LinkedIn scraping
- **GitHub** uses the official GitHub REST API
- **Stack Overflow** uses the official Stack Exchange API
- **Job Boards** are searched via Google X-Ray (`site:naukri.com`, etc.) — standard public search
- **Web CVs** are publicly accessible documents indexed by Google

Users are responsible for complying with applicable data privacy regulations (GDPR, etc.) when storing and processing candidate information.

---

## 🏗️ Built With

- [Streamlit](https://streamlit.io) — Frontend framework
- [Supabase](https://supabase.com) — Database & Authentication
- [Anthropic Claude](https://anthropic.com) — AI Intelligence Layer
- [Google Custom Search API](https://developers.google.com/custom-search) — X-Ray Sourcing
- [GitHub API](https://docs.github.com/en/rest) — Developer Sourcing
- [Stack Exchange API](https://api.stackexchange.com) — Expert Sourcing
- [Plotly](https://plotly.com) — Dashboard charts

---

*The Sourcer — AI Talent Intelligence Platform*
