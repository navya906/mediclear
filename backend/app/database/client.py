"""
Supabase client singleton.
All modules import get_supabase() to access the shared client.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    # Use service key to bypass RLS in the backend, fallback to anon key
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY (or ANON_KEY) must be set in backend/.env"
        )
    return create_client(url, key)


def fetch_one(query) -> Optional[dict]:
    """
    Execute a select query and return the first row, or None if no rows match.

    Use this instead of .single(), which raises an APIError (-> HTTP 500)
    when zero rows are found instead of letting callers return a 404.
    """
    rows = query.limit(1).execute().data
    return rows[0] if rows else None
