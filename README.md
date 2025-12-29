# cfb-tracker

Syncs college football recruiting and transfer portal data from On3 and 247Sports to Supabase. Designed to run as a cron job on Railway.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Supabase project
- GitHub PAT with access to `bowenaguero/cfb-cli`
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for webhooks)

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

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Create Railway project

1. Go to [Railway](https://railway.app) and create a new project
2. Select "Deploy from GitHub repo"
3. Connect your `cfb-tracker` repository
4. Railway will auto-detect the Dockerfile and build

### 3. Set environment variables

In Railway dashboard → Variables, add:

| Variable | Value |
|----------|-------|
| `GH_PAT` | Your GitHub PAT |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase service role key |
| `ON3_TEAM_NAME` | Team name for On3 (e.g., `auburn-tigers`) |
| `TEAM_247_NAME` | Team name for 247Sports (e.g., `auburn`) |
| `ON3_YEAR` | Recruiting year for On3 |
| `TEAM_247_YEAR` | Recruiting year for 247Sports |

### 4. Cron schedule

The service is configured to run every 30 minutes via `railway.toml`. To change the schedule, edit `cronSchedule` in that file.

## Webhooks (optional)

Send notifications to external services when records are added, updated, or deleted.

### 1. Install and link Supabase CLI

```bash
# Install Supabase CLI (macOS)
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase

# Login and link to your project
supabase login
supabase link --project-ref your-project-ref
```

### 2. Deploy the edge function

```bash
supabase functions deploy webhook-forwarder
```

### 3. Set edge function secrets

```bash
supabase secrets set RECRUITS_WEBHOOK_URL=https://your-webhook.com/recruits
supabase secrets set PORTAL_WEBHOOK_URL=https://your-webhook.com/portal
```

### 4. Create database webhooks

In Supabase Dashboard → Database → Webhooks:

1. Click "Create a new hook"
2. Configure:
   - **Name:** `recruits_webhook`
   - **Table:** `recruits`
   - **Events:** Insert, Update, Delete
   - **Type:** Supabase Edge Function
   - **Edge Function:** `webhook-forwarder`
3. Click "Create"
4. Repeat for the `portal` table

### Webhook payload

Your external endpoint will receive:

```json
{
  "event": "insert | update | delete",
  "table": "recruits",
  "record": { "entry_id": "abc123", "name": "john smith", ... },
  "old_record": { ... },
  "timestamp": "2025-12-29T12:00:00.000Z"
}
```

## How it works

1. **Fetches data** from On3 and 247Sports using cfb-cli
2. **Normalizes names** to handle variations across sources:
   - "DJ Smith" and "Derrick Smith" → same player
   - "John Smith Jr." and "John Smith, Jr" → same player
   - "Kensly Ladour-Foustin III" and "Kensley Foustin" → same player
3. **Merges with 247 as authoritative** - 247Sports data takes priority; On3 only fills gaps
4. **Syncs to Supabase** - upserts new/updated records, deletes players no longer in source data
5. **Logs in JSON format** for easy parsing in production

## Project structure

```
src/cfb_tracker/
├── main.py          # Entry point, orchestrates sync
├── config.py        # Environment variable loading
├── normalizer.py    # Name normalization and ID generation
├── fetcher.py       # Fetches and merges data from both sources
├── sync.py          # Syncs data to Supabase
└── db.py            # Supabase client wrapper

supabase/
├── functions/
│   └── webhook-forwarder/
│       └── index.ts    # Edge function for webhooks
└── migrations/
    └── 001_webhook_triggers.sql  # Database triggers
```
