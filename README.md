# Apple Media Fetcher

Daily Apple RSS rankings fetcher -> Supabase.

Fetches top-100 rankings from Apple's RSS Marketing Tools API for Apps, Music, Podcasts, Books, and Audiobooks across ~175 storefronts. 13 staggered cron jobs spaced ~2h apart to spread server load.

## Schedule

| Time UTC | Media | Content | Chart | Calls |
|---|---|---|---|---|
| 00:00 | apps | apps | top-free | 175 |
| 01:50 | apps | apps | top-paid | 175 |
| 03:40 | music | albums | most-played | 167 |
| 05:30 | music | music-videos | most-played | 167 |
| 07:20 | music | playlists | most-played | 167 |
| 09:10 | music | songs | most-played | 167 |
| 11:00 | podcasts | podcasts | top | 175 |
| 12:50 | podcasts | podcasts | top-subscriber | 175 |
| 14:40 | podcasts | podcast-episodes | top | 175 |
| 16:30 | podcasts | podcast-channels | top-subscriber | 175 |
| 18:20 | books | books | top-free | 154 |
| 20:10 | books | books | top-paid | 154 |
| 22:00 | audiobooks | audiobooks | top | 154 |

## Setup

1. Create a Supabase project
2. Run `migrations/001_initial.sql` in the Supabase SQL editor
3. Add `SUPABASE_URL` as a GitHub secret (the `postgresql://...` connection string)
4. Workflows run automatically on schedule

## Manual Trigger

Any workflow can be triggered manually from the GitHub Actions tab.
