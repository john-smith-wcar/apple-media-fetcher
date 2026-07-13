import os

import httpx


def _headers():
    key = os.environ["SUPABASE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base():
    return os.environ["SUPABASE_URL"].rstrip("/")


def upsert_media_items(items: list[dict]):
    if not items:
        return
    hdrs = _headers()
    hdrs["Prefer"] = "resolution=merge-duplicates"
    resp = httpx.post(
        f"{_base()}/media_items",
        headers=hdrs,
        json=items,
        params={"on_conflict": "id"},
    )
    resp.raise_for_status()


def insert_snapshots(snapshots: list[dict]):
    if not snapshots:
        return
    resp = httpx.post(
        f"{_base()}/ranking_snapshots",
        headers=_headers(),
        json=snapshots,
    )
    resp.raise_for_status()
