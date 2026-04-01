-- ============================================================
-- THE SOURCER — Signup Fix
-- Run this in Supabase SQL Editor (safe to run multiple times)
-- This fixes "database error saving new user" on signup
-- ============================================================

-- ── Step 1: Drop and recreate the trigger function with SECURITY DEFINER ──
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user();

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Insert profile row (ignore if already exists)
  INSERT INTO public.profiles (id, email, full_name, role, onboarding_completed)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    'user',
    FALSE
  )
  ON CONFLICT (id) DO NOTHING;

  -- Insert onboarding row (ignore if already exists)
  INSERT INTO public.onboarding (user_id, completed_steps)
  VALUES (NEW.id, '{}')
  ON CONFLICT (user_id) DO NOTHING;

  RETURN NEW;
END;
$$;

-- ── Step 2: Recreate the trigger ─────────────────────────────
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- ── Step 3: Fix RLS policies on profiles ─────────────────────
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
  ON public.profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ── Step 4: Fix RLS on onboarding table ──────────────────────
ALTER TABLE public.onboarding DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own onboarding" ON public.onboarding;

ALTER TABLE public.onboarding ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own onboarding"
  ON public.onboarding FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ── Step 5: Grant permissions ─────────────────────────────────
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ── Step 6: Verify trigger exists ────────────────────────────
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';
