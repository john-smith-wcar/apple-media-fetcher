ALTER TABLE ranking_snapshots
ADD CONSTRAINT uq_snapshot_per_day
UNIQUE (media_type, store_front, content_type, chart, snap_time);
