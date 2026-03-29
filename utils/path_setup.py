"""
utils/path_setup.py
CRITICAL for Streamlit Cloud: adds the project root to sys.path
so that imports like 'from core.auth import ...' work correctly.

Import this at the very top of every page file:
    from utils.path_setup import setup_path
    setup_path()

Or simpler — just call it inline:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
import sys
import os


def setup_path():
    """Ensure the project root is in sys.path."""
    # When running from pages/ subdirectory, the root may not be in path
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
