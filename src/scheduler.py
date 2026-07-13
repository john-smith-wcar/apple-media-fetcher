import os
import sys

from fetcher import run_media_fetch
from db import upsert_media_items, insert_snapshots


def main():
    media_type = os.environ.get("MEDIA_TYPE", "")
    content_type = os.environ.get("CONTENT_TYPE", "")
    chart = os.environ.get("CHART", "")

    if not (media_type and content_type and chart):
        print("Missing MEDIA_TYPE, CONTENT_TYPE, or CHART env vars")
        sys.exit(1)

    print(f"Fetching {media_type}/{content_type}/{chart} ...")
    result = run_media_fetch(media_type, content_type, chart)

    items = result["items"]
    snapshots = result["snapshots"]
    print(f"  Items: {len(items)}, Snapshots: {len(snapshots)}")

    upsert_media_items(items)
    print(f"  Upserted {len(items)} media items")

    insert_snapshots(snapshots)
    print(f"  Inserted {len(snapshots)} ranking snapshots")

    print("Done.")


if __name__ == "__main__":
    main()
