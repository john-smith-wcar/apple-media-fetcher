import os
import re
from datetime import datetime

import httpx

BATCH_SIZE = 500


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


def _post_batch(url: str, headers: dict, batch: list[dict], params: dict | None = None):
    resp = httpx.post(url, headers=headers, json=batch, params=params)
    if resp.status_code >= 400:
        raise RuntimeError(f"POST {url} {resp.status_code}: {resp.text[:500]}")


def upsert_media_items(items: list[dict]):
    if not items:
        return

    seen = set()
    deduped = []
    for item in items:
        iid = item["id"]
        if iid not in seen:
            seen.add(iid)
            deduped.append(item)

    serialized = []
    for item in deduped:
        it = dict(item)
        rd = it.get("release_date")
        if rd and isinstance(rd, str) and re.match(r"^\d{4}$", rd):
            it["release_date"] = f"{rd}-01-01T00:00:00Z"
        elif rd and isinstance(rd, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", rd):
            it["release_date"] = f"{rd}T00:00:00Z"
        serialized.append(it)

    hdrs = _headers()
    hdrs["Prefer"] = "resolution=merge-duplicates"
    url = f"{_base()}/media_items"
    params = {"on_conflict": "id"}
    for i in range(0, len(serialized), BATCH_SIZE):
        batch = serialized[i : i + BATCH_SIZE]
        _post_batch(url, hdrs, batch, params)
        print(f"  Upserted {min(i + BATCH_SIZE, len(serialized))}/{len(serialized)} media items")


def upsert_snapshots(snapshots: list[dict]):
    if not snapshots:
        return

    serialized = []
    for snap in snapshots:
        s = dict(snap)
        if isinstance(s.get("snap_time"), datetime):
            s["snap_time"] = s["snap_time"].isoformat()
        serialized.append(s)

    hdrs = _headers()
    hdrs["Prefer"] = "resolution=merge-duplicates"
    url = f"{_base()}/ranking_snapshots"
    params = {"on_conflict": "media_type,store_front,content_type,chart,snap_time"}
    for i in range(0, len(serialized), BATCH_SIZE):
        batch = serialized[i : i + BATCH_SIZE]
        _post_batch(url, hdrs, batch, params)
        print(f"  Upserted {min(i + BATCH_SIZE, len(serialized))}/{len(serialized)} ranking snapshots")
