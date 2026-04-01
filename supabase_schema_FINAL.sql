-- ============================================================
-- THE SOURCER — Complete Supabase Schema (Final Version)
-- Run this ONCE in Supabase SQL Editor
-- Safe to re-run — uses IF NOT EXISTS / ON CONFLICT DO NOTHING
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── TEAMS ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name       TEXT NOT NULL,
    owner_id   UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── USER PROFILES ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
    id                    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email                 TEXT NOT NULL,
    full_name             TEXT,
    role                  TEXT DEFAULT 'user' CHECK (role IN ('user','admin')),
    company               TEXT,
    job_title             TEXT,
    team_id               UUID REFERENCES teams(id),
    onboarding_completed  BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ── API KEYS (multi-provider) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE UNIQUE,
    -- AI providers (user picks one or more)
    ai_provider     TEXT DEFAULT 'anthropic',   -- anthropic | openai | groq | mistral
    anthropic_key   TEXT,
    openai_key      TEXT,
    groq_key        TEXT,
    mistral_key     TEXT,
    -- Search providers
    google_api_key  TEXT,
    google_cse_id   TEXT,
    serp_api_key    TEXT,                        -- SerpAPI alternative to Google CSE
    -- Developer sourcing
    github_token    TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── JD LIBRARY ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jd_library (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    jd_text      TEXT NOT NULL,
    ai_analysis  JSONB,
    skill_matrix JSONB,
    tags         TEXT[],
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── SEARCHES ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS searches (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    jd_id          UUID REFERENCES jd_library(id),
    name           TEXT NOT NULL,
    filters        JSONB NOT NULL DEFAULT '{}',
    sources        JSONB NOT NULL DEFAULT '[]',
    boolean_strings JSONB,
    result_count   INTEGER DEFAULT 0,
    status         TEXT DEFAULT 'completed' CHECK (status IN ('draft','running','completed','paused')),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── CANDIDATES ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidates (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    team_id          UUID REFERENCES teams(id),
    search_id        UUID REFERENCES searches(id),
    full_name        TEXT,
    current_title    TEXT,
    location         TEXT,
    source           TEXT NOT NULL,
    profile_url      TEXT,
    email            TEXT,
    skills           TEXT[],
    experience_years INTEGER,
    summary          TEXT,
    match_score      INTEGER DEFAULT 0,
    stage            TEXT DEFAULT 'sourced'
                     CHECK (stage IN ('sourced','reviewed','contacted','responded','interview','rejected')),
    notes            TEXT,
    is_shared        BOOLEAN DEFAULT FALSE,
    raw_data         JSONB,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── OUTREACH LOG ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS outreach_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    candidate_id    UUID REFERENCES candidates(id) ON DELETE CASCADE,
    message_text    TEXT NOT NULL,
    message_format  TEXT DEFAULT 'linkedin',
    tone            TEXT DEFAULT 'professional',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── ONBOARDING ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS onboarding (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE UNIQUE,
    completed_steps TEXT[] DEFAULT '{}',
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── TEAM MEMBERS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_members (
    id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id   UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id   UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role      TEXT DEFAULT 'member' CHECK (role IN ('owner','admin','member')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (team_id, user_id)
);

-- ── ROW LEVEL SECURITY ──────────────────────────────────────────
ALTER TABLE profiles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys     ENABLE ROW LEVEL SECURITY;
ALTER TABLE jd_library   ENABLE ROW LEVEL SECURITY;
ALTER TABLE searches     ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates   ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding   ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams        ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

-- Profiles
DROP POLICY IF EXISTS "profiles_select_own"  ON profiles;
DROP POLICY IF EXISTS "profiles_insert_own"  ON profiles;
DROP POLICY IF EXISTS "profiles_update_own"  ON profiles;
DROP POLICY IF EXISTS "profiles_admin_all"   ON profiles;
CREATE POLICY "profiles_select_own"  ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_insert_own"  ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_update_own"  ON profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_admin_all"   ON profiles FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
);

-- API Keys
DROP POLICY IF EXISTS "apikeys_own" ON api_keys;
CREATE POLICY "apikeys_own" ON api_keys FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- JD Library
DROP POLICY IF EXISTS "jdlib_own" ON jd_library;
CREATE POLICY "jdlib_own" ON jd_library FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Searches
DROP POLICY IF EXISTS "searches_own" ON searches;
CREATE POLICY "searches_own" ON searches FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Candidates
DROP POLICY IF EXISTS "candidates_own"    ON candidates;
DROP POLICY IF EXISTS "candidates_shared" ON candidates;
CREATE POLICY "candidates_own"    ON candidates FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "candidates_shared" ON candidates FOR SELECT USING (
    is_shared = TRUE AND team_id IN (
        SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
);

-- Outreach
DROP POLICY IF EXISTS "outreach_own" ON outreach_log;
CREATE POLICY "outreach_own" ON outreach_log FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Onboarding
DROP POLICY IF EXISTS "onboarding_own" ON onboarding;
CREATE POLICY "onboarding_own" ON onboarding FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Teams
DROP POLICY IF EXISTS "teams_member_view" ON teams;
DROP POLICY IF EXISTS "teams_owner_update" ON teams;
DROP POLICY IF EXISTS "teams_insert" ON teams;
CREATE POLICY "teams_member_view"  ON teams FOR SELECT USING (
    id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
);
CREATE POLICY "teams_owner_update" ON teams FOR UPDATE USING (owner_id = auth.uid());
CREATE POLICY "teams_insert"       ON teams FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Team members
DROP POLICY IF EXISTS "members_view" ON team_members;
CREATE POLICY "members_view" ON team_members FOR SELECT USING (
    team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
);

-- ── TRIGGER: auto-create profile on signup ──────────────────────
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role, onboarding_completed)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        'user',
        FALSE
    )
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO public.onboarding (user_id, completed_steps)
    VALUES (NEW.id, '{}')
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ── PERMISSIONS ─────────────────────────────────────────────────
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL   ON ALL TABLES    IN SCHEMA public TO postgres, service_role;
GRANT ALL   ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES   IN SCHEMA public TO anon;

-- ── INDEXES ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_candidates_user    ON candidates(user_id);
CREATE INDEX IF NOT EXISTS idx_candidates_search  ON candidates(search_id);
CREATE INDEX IF NOT EXISTS idx_candidates_stage   ON candidates(stage);
CREATE INDEX IF NOT EXISTS idx_searches_user      ON searches(user_id);
CREATE INDEX IF NOT EXISTS idx_jdlib_user         ON jd_library(user_id);

-- ── VERIFY ──────────────────────────────────────────────────────
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
