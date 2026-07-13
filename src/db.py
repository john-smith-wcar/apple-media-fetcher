import os

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

    hdrs = _headers()
    hdrs["Prefer"] = "resolution=merge-duplicates"
    url = f"{_base()}/media_items"
    params = {"on_conflict": "id"}
    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i : i + BATCH_SIZE]
        _post_batch(url, hdrs, batch, params)
        print(f"  Upserted {min(i + BATCH_SIZE, len(deduped))}/{len(deduped)} media items")


def insert_snapshots(snapshots: list[dict]):
    if not snapshots:
        return
    headers = _headers()
    url = f"{_base()}/ranking_snapshots"
    for i in range(0, len(snapshots), BATCH_SIZE):
        batch = snapshots[i : i + BATCH_SIZE]
        _post_batch(url, headers, batch)
        print(f"  Inserted {min(i + BATCH_SIZE, len(snapshots))}/{len(snapshots)} ranking snapshots")
