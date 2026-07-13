CREATE TABLE IF NOT EXISTS media_items (
  id          TEXT PRIMARY KEY,
  media_type  TEXT NOT NULL,
  name        TEXT,
  artist_name TEXT,
  artwork_url TEXT,
  url         TEXT,
  genres      JSONB,
  release_date TIMESTAMPTZ,
  raw         JSONB,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_items_media_type ON media_items(media_type);
CREATE INDEX IF NOT EXISTS idx_media_items_name ON media_items(name);

CREATE TABLE IF NOT EXISTS ranking_snapshots (
  id           BIGSERIAL PRIMARY KEY,
  media_type   TEXT NOT NULL,
  store_front  TEXT NOT NULL,
  content_type TEXT NOT NULL,
  chart        TEXT NOT NULL,
  snap_time    TIMESTAMPTZ NOT NULL,
  rank_ids     JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rankings_lookup
  ON ranking_snapshots(media_type, store_front, content_type, chart, snap_time DESC);
