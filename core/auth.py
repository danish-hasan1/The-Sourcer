"""
core/auth.py
Authentication logic for The Sourcer using Supabase Auth.
"""
import streamlit as st
from core.database import get_supabase, get_profile, get_api_keys
from typing import Optional, Dict
import time


def sign_up(email: str, password: str, full_name: str) -> Dict:
    """Register a new user."""
    try:
        sb = get_supabase()
        res = sb.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })

        if res.user:
            return {"success": True, "user": res.user}

        return {"success": False, "error": "Signup failed. Please try again."}

    except Exception as e:
        err = str(e)
        if "already registered" in err.lower() or "already exists" in err.lower():
            return {"success": False, "error": "This email is already registered. Please log in."}
        if "database error" in err.lower():
            return {
                "success": False,
                "error": "Database setup issue. Please ask the admin to run the signup_fix.sql script in Supabase."
            }
        return {"success": False, "error": f"Signup error: {err}"}


def sign_in(email: str, password: str) -> Dict:
    """Log in an existing user."""
    try:
        sb = get_supabase()
        res = sb.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if res.user and res.session:
            return {"success": True, "user": res.user, "session": res.session}

        return {"success": False, "error": "Invalid email or password."}

    except Exception as e:
        err = str(e)
        if "invalid" in err.lower() or "credentials" in err.lower():
            return {"success": False, "error": "Invalid email or password."}
        return {"success": False, "error": f"Login error: {err}"}


def sign_out():
    """Log out the current user."""
    try:
        sb = get_supabase()
        sb.auth.sign_out()
    except Exception:
        pass

    # Clear all session state
    keys_to_clear = ["user", "profile", "api_keys", "supabase_client",
                     "ai_results", "search_filters", "sourcing_results",
                     "search_id", "current_jd_id", "outreach_candidate"]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    st.rerun()


def get_current_user() -> Optional[Dict]:
    """Return the current user from session state."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    return "user" in st.session_state and st.session_state.user is not None


def is_admin() -> bool:
    profile = st.session_state.get("profile", {})
    return (profile or {}).get("role") == "admin"


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.switch_page("pages/01_Login.py")


def load_user_session(user_id: str):
    """
    Load profile and API keys into session state.
    If profile doesn't exist yet (trigger may be slow), create it manually.
    """
    if "profile" not in st.session_state or not st.session_state.get("profile"):
        profile = get_profile(user_id)

        # If trigger hasn't fired yet, wait briefly and retry
        if not profile:
            time.sleep(1)
            profile = get_profile(user_id)

        # If still no profile, create it manually as fallback
        if not profile:
            _create_profile_fallback(user_id)
            time.sleep(0.5)
            profile = get_profile(user_id)

        st.session_state.profile = profile or {}

    if "api_keys" not in st.session_state or not st.session_state.get("api_keys"):
        st.session_state.api_keys = get_api_keys(user_id) or {}


def _create_profile_fallback(user_id: str):
    """
    Manually create profile + onboarding rows if the trigger didn't fire.
    This is a safety net for when the Supabase trigger is slow or misconfigured.
    """
    try:
        sb = get_supabase()
        user_data = sb.auth.get_user()
        email = ""
        full_name = ""

        if user_data and user_data.user:
            email = user_data.user.email or ""
            meta = user_data.user.user_metadata or {}
            full_name = meta.get("full_name", "")

        # Insert profile using service role bypass via RPC
        # Falls back to direct insert if user has permission
        sb.table("profiles").upsert({
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": "user",
            "onboarding_completed": False,
        }, on_conflict="id").execute()

        sb.table("onboarding").upsert({
            "user_id": user_id,
            "completed_steps": [],
        }, on_conflict="user_id").execute()

    except Exception as e:
        # Silent fail — the user is still logged in, profile just won't load
        pass


def reset_password(email: str) -> Dict:
    """Send password reset email."""
    try:
        sb = get_supabase()
        sb.auth.reset_password_email(email)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_anthropic_key() -> Optional[str]:
    """Get the user's Anthropic API key from session or secrets."""
    keys = st.session_state.get("api_keys") or {}
    return keys.get("anthropic_key") or st.secrets.get("ANTHROPIC_KEY_DEFAULT", None)


def get_groq_key() -> Optional[str]:
    """Get the Groq API key from secrets."""
    from config import GROQ_API_KEY
    return GROQ_API_KEY


def get_google_keys() -> Dict:
    """Get Google CSE credentials."""
    keys = st.session_state.get("api_keys") or {}
    return {
        "cse_id": keys.get("google_cse_id", ""),
        "api_key": keys.get("google_api_key", ""),
    }


def get_github_token() -> Optional[str]:
    keys = st.session_state.get("api_keys") or {}
    return keys.get("github_token", "")
