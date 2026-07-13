import asyncio
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

API_BASE = "https://rss.marketingtools.apple.com/api/v2"
FETCH_LIMIT = 100
CONCURRENCY = 5
BATCH_DELAY = 0.5
MAX_RETRIES = 5

FEED_DIR = Path(__file__).resolve().parent.parent / "feed_settings"


def load_feed_setting(media_type: str):
    filename = "audio-books.json" if media_type == "audiobooks" else f"{media_type}.json"
    path = FEED_DIR / filename
    with open(path) as f:
        return json.load(f)


def build_tasks(media_type: str, content_type: str, chart: str):
    setting = load_feed_setting(media_type)
    storefronts = [s["value"] for s in setting["storefronts"]]
    random.shuffle(storefronts)
    tasks = []
    for sf in storefronts:
        api_media = sf_map(media_type)
        api_content = sf_map(content_type)
        tasks.append((sf, api_media, chart, api_content))
    return tasks


def sf_map(slug: str) -> str:
    mappings = {"audiobooks": "audio-books"}
    return mappings.get(slug, slug)


def build_url(storefront: str, api_media: str, chart: str, api_content: str) -> str:
    return f"{API_BASE}/{storefront}/{api_media}/{chart}/{FETCH_LIMIT}/{api_content}.json"


async def fetch_single(client: httpx.AsyncClient, url: str) -> dict | None:
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(url, headers={"User-Agent": "AppleMediaFetcher/1.0"})
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 502, 503, 504):
                wait = min(2 ** (attempt + 1), 30)
                await asyncio.sleep(wait)
                continue
            return None
        except (httpx.TimeoutException, httpx.ConnectError):
            if attempt == MAX_RETRIES:
                return None
            await asyncio.sleep(2 ** attempt)
    return None


def parse_items(media_type: str, data: dict) -> list[dict]:
    feed = data.get("feed", {})
    entries = feed.get("results", []) if "results" in feed else feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    items = []
    for entry in entries:
        item_id = entry.get("id") or entry.get("id", {}).get("attributes", {}).get("im:id")
        if not item_id:
            continue
        name = (entry.get("im:name", {}) or {}).get("label") or entry.get("name", {}).get("label") or entry.get("collectionName") or entry.get("trackName")
        artist = (entry.get("im:artist", {}) or {}).get("label") or entry.get("artistName")
        artwork = None
        for key in ("im:image", "artworkUrl100", "artworkUrl60"):
            val = entry.get(key)
            if val:
                artwork = val[-1]["label"] if isinstance(val, list) and isinstance(val[0], dict) else val
                break
        link = None
        for key in ("link", "trackViewUrl", "collectionViewUrl"):
            val = entry.get(key)
            if val:
                link = val[0]["attributes"]["href"] if isinstance(val, list) and isinstance(val[0], dict) else val
                break
        genres = []
        category = entry.get("category", {}) or {}
        if isinstance(category, dict):
            attrs = category.get("attributes", {})
            if attrs:
                genres.append(attrs.get("label") or attrs.get("term") or "")
            else:
                genre_entry = entry.get("im:genre", [])
                if isinstance(genre_entry, list):
                    genres = [g.get("label", "") for g in genre_entry if isinstance(g, dict)]
                elif isinstance(genre_entry, dict):
                    genres.append(genre_entry.get("label", ""))
        release = entry.get("im:releaseDate", {}).get("label") if isinstance(entry.get("im:releaseDate"), dict) else entry.get("releaseDate")
        items.append({
            "id": str(item_id),
            "media_type": media_type,
            "name": str(name or ""),
            "artist_name": str(artist or ""),
            "artwork_url": str(artwork or ""),
            "url": str(link or ""),
            "genres": json.dumps(genres),
            "release_date": release,
        })
    return items


def parse_rank_ids(data: dict) -> list[str]:
    feed = data.get("feed", {})
    entries = feed.get("results", []) if "results" in feed else feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    ids = []
    for entry in entries:
        item_id = entry.get("id") or entry.get("id", {}).get("attributes", {}).get("im:id")
        if item_id:
            ids.append(str(item_id))
    return ids


async def run_media_fetch(media_type: str, content_type: str, chart: str) -> dict:
    tasks = build_tasks(media_type, content_type, chart)
    snap_time = datetime.now(timezone.utc)

    async with httpx.AsyncClient(timeout=30.0) as client:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bounded_fetch(storefront, api_media, chart, api_content):
            async with sem:
                url = build_url(storefront, api_media, chart, api_content)
                data = await fetch_single(client, url)
                if not data:
                    return storefront, None, None
                items = parse_items(media_type, data)
                rank_ids = parse_rank_ids(data)
                return storefront, items, rank_ids

        all_items = []
        snapshots = []
        batch = []
        for storefront, api_media, chart_slug, api_content in tasks:
            batch.append(bounded_fetch(storefront, api_media, chart_slug, api_content))
            if len(batch) >= CONCURRENCY:
                for sf, items, rank_ids in await asyncio.gather(*batch):
                    if items is not None:
                        all_items.extend(items)
                        snapshots.append({
                            "media_type": media_type,
                            "store_front": sf,
                            "content_type": content_type,
                            "chart": chart,
                            "snap_time": snap_time,
                            "rank_ids": rank_ids,
                        })
                batch = []
                await asyncio.sleep(BATCH_DELAY)

        if batch:
            for sf, items, rank_ids in await asyncio.gather(*batch):
                if items is not None:
                    all_items.extend(items)
                    snapshots.append({
                        "media_type": media_type,
                        "store_front": sf,
                        "content_type": content_type,
                        "chart": chart,
                        "snap_time": snap_time,
                        "rank_ids": rank_ids,
                    })

    return {"media_type": media_type, "items": all_items, "snapshots": snapshots}
