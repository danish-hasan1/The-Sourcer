"""
db.py — SQLite schema + all queries for the candidate search engine.

Tables:
  jobs          — one row per sourcing engagement (JD + filter config)
  candidates    — one row per unique person found
  job_candidates — many-to-many: which candidates were found for which job
  outreach      — email outreach history per candidate per job
"""

import sqlite3
import json
from datetime import datetime
from config import DB_PATH


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # safe for Streamlit multi-thread
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    jd_text         TEXT,
    jd_url          TEXT,

    -- Prompt chain outputs (stored as JSON strings)
    p1_analysis     TEXT,   -- Prompt 1 full output
    p2_matrix       TEXT,   -- Prompt 2 full output
    p3_params       TEXT,   -- Prompt 3 full output

    -- Parsed filter config (JSON)
    filter_config   TEXT,   -- {titles, must_skills, nice_skills, exp_range,
                            --  seniority, location, industry, exclude, sources}
    boolean_string  TEXT,

    status          TEXT    DEFAULT 'draft',  -- draft | active | closed
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS candidates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT,
    current_title   TEXT,
    current_company TEXT,
    location        TEXT,
    email           TEXT,
    phone           TEXT,
    linkedin_url    TEXT    UNIQUE,
    github_url      TEXT,
    profile_summary TEXT,
    skills          TEXT,   -- JSON array
    experience_years REAL,
    source          TEXT,   -- linkedin | github | naukri | google
    source_url      TEXT,
    raw_profile     TEXT,   -- full scraped HTML/text
    last_verified   TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_candidates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id    INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    match_score     REAL,           -- 0–100 from AI scorer
    score_breakdown TEXT,           -- JSON: {skill_score, exp_score, ...}
    stage           TEXT DEFAULT 'found',  -- found | shortlisted | contacted | responded | rejected
    notes           TEXT,
    added_at        TEXT DEFAULT (datetime('now')),
    UNIQUE(job_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS outreach (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id    INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    email_to        TEXT,
    subject         TEXT,
    body            TEXT,
    sent_at         TEXT,
    opened_at       TEXT,
    replied_at      TEXT,
    status          TEXT DEFAULT 'draft'  -- draft | sent | opened | replied | bounced
);

CREATE INDEX IF NOT EXISTS idx_jc_job      ON job_candidates(job_id);
CREATE INDEX IF NOT EXISTS idx_jc_cand     ON job_candidates(candidate_id);
CREATE INDEX IF NOT EXISTS idx_cand_li     ON candidates(linkedin_url);
CREATE INDEX IF NOT EXISTS idx_outreach_jc ON outreach(job_id, candidate_id);
"""


def init_db():
    """Create all tables if they don't exist. Safe to call on every startup."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def create_job(title: str, jd_text: str = "", jd_url: str = "") -> int:
    """Insert a new job and return its id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (title, jd_text, jd_url) VALUES (?,?,?)",
            (title, jd_text, jd_url)
        )
        return cur.lastrowid


def update_job_chain_outputs(job_id: int, p1: str, p2: str, p3: str):
    """Save the raw prompt chain outputs."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE jobs SET p1_analysis=?, p2_matrix=?, p3_params=?,
               updated_at=datetime('now') WHERE id=?""",
            (p1, p2, p3, job_id)
        )


def update_job_filters(job_id: int, filter_config: dict, boolean_string: str):
    """Save the parsed filter config and boolean string."""
    with get_conn() as conn:
        conn.execute(
            """UPDATE jobs SET filter_config=?, boolean_string=?,
               updated_at=datetime('now') WHERE id=?""",
            (json.dumps(filter_config), boolean_string, job_id)
        )


def get_job(job_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        for field in ("filter_config",):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    pass
        return d


def list_jobs() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, status, created_at FROM jobs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_job_status(job_id: int, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, updated_at=datetime('now') WHERE id=?",
            (status, job_id)
        )


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

def upsert_candidate(data: dict) -> int:
    """
    Insert or update a candidate by linkedin_url (unique key).
    Returns the candidate id.
    """
    skills = json.dumps(data.get("skills", []))
    with get_conn() as conn:
        # Try update first
        if data.get("linkedin_url"):
            conn.execute(
                """INSERT INTO candidates
                   (full_name, current_title, current_company, location,
                    email, phone, linkedin_url, github_url, profile_summary,
                    skills, experience_years, source, source_url, raw_profile, last_verified)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(linkedin_url) DO UPDATE SET
                     full_name=excluded.full_name,
                     current_title=excluded.current_title,
                     current_company=excluded.current_company,
                     location=excluded.location,
                     email=coalesce(excluded.email, email),
                     skills=excluded.skills,
                     last_verified=datetime('now')""",
                (
                    data.get("full_name"), data.get("current_title"),
                    data.get("current_company"), data.get("location"),
                    data.get("email"), data.get("phone"),
                    data.get("linkedin_url"), data.get("github_url"),
                    data.get("profile_summary"), skills,
                    data.get("experience_years"), data.get("source"),
                    data.get("source_url"), data.get("raw_profile"),
                )
            )
            row = conn.execute(
                "SELECT id FROM candidates WHERE linkedin_url=?",
                (data["linkedin_url"],)
            ).fetchone()
            return row["id"]
        else:
            cur = conn.execute(
                """INSERT INTO candidates
                   (full_name, current_title, current_company, location,
                    email, phone, github_url, profile_summary,
                    skills, experience_years, source, source_url, raw_profile, last_verified)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
                (
                    data.get("full_name"), data.get("current_title"),
                    data.get("current_company"), data.get("location"),
                    data.get("email"), data.get("phone"),
                    data.get("github_url"), data.get("profile_summary"),
                    skills, data.get("experience_years"),
                    data.get("source"), data.get("source_url"), data.get("raw_profile"),
                )
            )
            return cur.lastrowid


def link_candidate_to_job(job_id: int, candidate_id: int,
                           match_score: float = 0.0,
                           score_breakdown: dict = None):
    """Add candidate to a job's pool. Ignore if already linked."""
    with get_conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO job_candidates
               (job_id, candidate_id, match_score, score_breakdown)
               VALUES (?,?,?,?)""",
            (job_id, candidate_id, match_score,
             json.dumps(score_breakdown or {}))
        )


def get_job_candidates(job_id: int, stage: str = None) -> list[dict]:
    """Return candidates for a job, optionally filtered by stage, sorted by score."""
    with get_conn() as conn:
        query = """
            SELECT c.*, jc.match_score, jc.score_breakdown, jc.stage, jc.notes
            FROM candidates c
            JOIN job_candidates jc ON jc.candidate_id = c.id
            WHERE jc.job_id = ?
        """
        params = [job_id]
        if stage:
            query += " AND jc.stage = ?"
            params.append(stage)
        query += " ORDER BY jc.match_score DESC"
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for field in ("skills", "score_breakdown"):
                if d.get(field):
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        pass
            results.append(d)
        return results


def update_candidate_stage(job_id: int, candidate_id: int, stage: str, notes: str = None):
    with get_conn() as conn:
        conn.execute(
            """UPDATE job_candidates SET stage=?, notes=coalesce(?,notes)
               WHERE job_id=? AND candidate_id=?""",
            (stage, notes, job_id, candidate_id)
        )


def search_candidates_in_db(query: str, filters: dict) -> list[dict]:
    """
    Full-text search across the candidate DB using filters.
    Used for 'score existing DB' mode.
    """
    with get_conn() as conn:
        sql = "SELECT * FROM candidates WHERE 1=1"
        params = []

        if query:
            sql += """ AND (full_name LIKE ? OR current_title LIKE ?
                       OR profile_summary LIKE ? OR skills LIKE ?)"""
            q = f"%{query}%"
            params.extend([q, q, q, q])

        if filters.get("location"):
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")

        if filters.get("min_exp"):
            sql += " AND experience_years >= ?"
            params.append(filters["min_exp"])

        sql += " ORDER BY created_at DESC LIMIT 200"
        rows = conn.execute(sql, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("skills"):
                try:
                    d["skills"] = json.loads(d["skills"])
                except Exception:
                    pass
            results.append(d)
        return results


# ---------------------------------------------------------------------------
# Outreach
# ---------------------------------------------------------------------------

def save_outreach_draft(job_id: int, candidate_id: int,
                        email_to: str, subject: str, body: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO outreach (job_id, candidate_id, email_to, subject, body)
               VALUES (?,?,?,?,?)""",
            (job_id, candidate_id, email_to, subject, body)
        )
        return cur.lastrowid


def mark_outreach_sent(outreach_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE outreach SET status='sent', sent_at=datetime('now') WHERE id=?",
            (outreach_id,)
        )
