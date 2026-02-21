"""
config.py — Supabase HTTP client using direct REST API calls.
Avoids SDK dependency hell on Python 3.14.
"""

import httpx
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    supabase_url: str = os.environ["SUPABASE_URL"]
    supabase_anon_key: str = os.environ["SUPABASE_ANON_KEY"]
    supabase_service_key: str = os.environ["SUPABASE_SERVICE_KEY"]
    supabase_jwt_secret: str = os.environ["SUPABASE_JWT_SECRET"]
    frontend_url: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_db(admin: bool = True) -> "SupabaseDB":
    """Returns an http-based DB client."""
    return SupabaseDB(admin=admin)


class SupabaseDB:
    """
    Lightweight Supabase PostgREST client using httpx.
    Supports select, insert, update, delete, upsert with simple chaining.
    """

    def __init__(self, admin: bool = True):
        s = get_settings()
        self._base = f"{s.supabase_url}/rest/v1"
        key = s.supabase_service_key if admin else s.supabase_anon_key
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # ── Core ─────────────────────────────────────────────────────────────────

    def _url(self, table: str) -> str:
        return f"{self._base}/{table}"

    def select(self, table: str, columns: str = "*", filters: dict | None = None,
               order: str | None = None, limit: int | None = None, single: bool = False) -> list | dict | None:
        params: dict = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        headers = dict(self._headers)
        if single:
            headers["Accept"] = "application/vnd.pgrst.object+json"
        with httpx.Client() as client:
            r = client.get(self._url(table), params=params, headers=headers)
            if r.status_code == 406:
                return None  # single row not found
            r.raise_for_status()
            return r.json()

    def insert(self, table: str, data: dict | list) -> list:
        with httpx.Client() as client:
            r = client.post(self._url(table), json=data, headers=self._headers)
            r.raise_for_status()
            return r.json()

    def update(self, table: str, data: dict, filters: dict) -> list:
        params = dict(filters)
        with httpx.Client() as client:
            r = client.patch(self._url(table), json=data, params=params, headers=self._headers)
            r.raise_for_status()
            return r.json()

    def delete(self, table: str, filters: dict) -> list:
        params = dict(filters)
        with httpx.Client() as client:
            r = client.delete(self._url(table), params=params, headers=self._headers)
            r.raise_for_status()
            return r.json()

    def upsert(self, table: str, data: dict | list, on_conflict: str = "id") -> list:
        headers = dict(self._headers)
        headers["Prefer"] = f"return=representation,resolution=merge-duplicates"
        params = {"on_conflict": on_conflict}
        with httpx.Client() as client:
            r = client.post(self._url(table), json=data, params=params, headers=headers)
            r.raise_for_status()
            return r.json()

    # ── Auth helpers ─────────────────────────────────────────────────────────

    def auth_signup(self, email: str, password: str, metadata: dict | None = None) -> dict:
        s = get_settings()
        url = f"{s.supabase_url}/auth/v1/signup"
        body = {"email": email, "password": password}
        if metadata:
            body["data"] = metadata
        headers = {
            "apikey": s.supabase_anon_key,
            "Content-Type": "application/json",
        }
        with httpx.Client() as client:
            r = client.post(url, json=body, headers=headers)
            if not r.is_success:
                try:
                    data = r.json()
                    msg = data.get("error_description") or data.get("msg") or data.get("message") or r.text
                except Exception:
                    msg = r.text
                raise Exception(msg)
            return r.json()

    def auth_login(self, email: str, password: str) -> dict:
        s = get_settings()
        url = f"{s.supabase_url}/auth/v1/token?grant_type=password"
        body = {"email": email, "password": password}
        headers = {
            "apikey": s.supabase_anon_key,
            "Content-Type": "application/json",
        }
        with httpx.Client() as client:
            r = client.post(url, json=body, headers=headers)
            if not r.is_success:
                try:
                    data = r.json()
                    msg = data.get("error_description") or data.get("msg") or data.get("message") or r.text
                except Exception:
                    msg = r.text
                raise Exception(msg)
            return r.json()
