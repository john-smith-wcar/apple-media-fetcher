import os

import psycopg2
import psycopg2.extras


def get_conn():
    return psycopg2.connect(os.environ["SUPABASE_URL"])


def upsert_media_items(items: list[dict]):
    if not items:
        return
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            args = []
            for i in items:
                args.append((
                    i["id"],
                    i["media_type"],
                    i["name"],
                    i["artist_name"],
                    i["artwork_url"],
                    i["url"],
                    i.get("genres"),
                    i.get("release_date"),
                    psycopg2.extras.Json(i.get("raw", {})),
                ))
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO media_items (id, media_type, name, artist_name, artwork_url, url, genres, release_date, raw, updated_at)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                  name = EXCLUDED.name,
                  artist_name = EXCLUDED.artist_name,
                  artwork_url = EXCLUDED.artwork_url,
                  url = EXCLUDED.url,
                  genres = EXCLUDED.genres,
                  release_date = EXCLUDED.release_date,
                  raw = EXCLUDED.raw,
                  updated_at = NOW()
                """,
                args,
            )
        conn.commit()
    finally:
        conn.close()


def insert_snapshots(snapshots: list[dict]):
    if not snapshots:
        return
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            args = []
            for s in snapshots:
                args.append((
                    s["media_type"],
                    s["store_front"],
                    s["content_type"],
                    s["chart"],
                    s["snap_time"],
                    psycopg2.extras.Json(s["rank_ids"]),
                ))
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO ranking_snapshots (media_type, store_front, content_type, chart, snap_time, rank_ids)
                VALUES %s
                """,
                args,
            )
        conn.commit()
    finally:
        conn.close()
