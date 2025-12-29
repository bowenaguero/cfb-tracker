# cfb-tracker

Syncs college football recruiting and transfer portal data from On3 and 247Sports to Supabase. Designed to run as a cron job on Railway.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Supabase project
- GitHub PAT with access to `bowenaguero/cfb-cli`

## Setup

### 1. Clone and install

```bash
git clone https://github.com/bowenaguero/cfb-tracker.git
cd cfb-tracker
uv sync
```

### 2. Create Supabase tables

Run this SQL in your Supabase dashboard (SQL Editor):

```sql
CREATE TABLE IF NOT EXISTS recruits (
    id bigint generated always as identity primary key,
    entry_id text unique not null,
    name text,
    position text,
    hometown text,
    stars int,
    rating float,
    status text,
    source text,
    updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS portal (
    id bigint generated always as identity primary key,
    entry_id text unique not null,
    name text,
    position text,
    direction text,
    status text,
    source text,
    updated_at timestamptz
);

ALTER TABLE recruits ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal ENABLE ROW LEVEL SECURITY;
```

### 3. Configure environment

Create a `.env` file:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Team names (as they appear in URLs)
ON3_TEAM_NAME=auburn-tigers
TEAM_247_NAME=auburn

# Recruiting years
ON3_YEAR=2026
TEAM_247_YEAR=2026
```

### 4. Install cfb-cli

```bash
uv pip install git+https://<YOUR_GH_PAT>@github.com/bowenaguero/cfb-cli.git
```

### 5. Run locally

```bash
uv run python -m cfb_tracker.main
```

## Deploy to Railway

### 1. Push to GitHub

### 2. Create Railway project

- Connect your GitHub repo
- Railway will auto-detect the Dockerfile

### 3. Set environment variables

In Railway dashboard, add:

| Variable | Value |
|----------|-------|
| `GH_PAT` | Your GitHub PAT |
| `SUPABASE_URL` | Your Supabase URL |
| `SUPABASE_KEY` | Your Supabase service role key |
| `ON3_TEAM_NAME` | Team name for On3 |
| `TEAM_247_NAME` | Team name for 247Sports |
| `ON3_YEAR` | Recruiting year |
| `TEAM_247_YEAR` | Recruiting year |

### 4. Configure cron

In Railway service settings, set up a cron schedule (e.g., `0 * * * *` for hourly).

## How it works

1. Fetches recruit/portal data from On3 and 247Sports using cfb-cli
2. Normalizes player names to handle variations (e.g., "DJ Smith" vs "Derrick Smith")
3. Merges data from both sources (higher ratings win, tracks which sources have the player)
4. Syncs to Supabase: upserts new/updated records, deletes players no longer in source data
