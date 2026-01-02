# cfb-tracker

Syncs college football recruiting and transfer portal data from 247Sports to Supabase. Designed to run as a cron job on Railway.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Supabase project
- GitHub PAT with access to `bowenaguero/cfb-cli`
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for webhooks, optional)
- Redis instance (for social media queue, optional)

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
    source_school text,
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

# 247Sports configuration
TEAM_247_NAME=auburn
TEAM_247_YEAR=2026

# Team display name (for social media posts)
TEAM="Auburn Tigers"

# Redis (optional - for social media queue)
REDIS_URL=redis://localhost:6379
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

| Variable        | Value                                                   |
| --------------- | ------------------------------------------------------- |
| `GH_PAT`        | Your GitHub PAT                                         |
| `SUPABASE_URL`  | Your Supabase project URL                               |
| `SUPABASE_KEY`  | Your Supabase service role key                          |
| `TEAM_247_NAME` | Team name for 247Sports (e.g., `auburn`)                |
| `TEAM_247_YEAR` | Recruiting year for 247Sports                           |
| `TEAM`          | Team display name (e.g., `Auburn Tigers`)               |
| `REDIS_URL`     | Redis connection URL (optional, for social media queue) |

### 4. Cron schedule

The service is configured to run every 10 minutes via `railway.toml`. To change the schedule, edit `cronSchedule` in that file.

## Social Media Queue (optional)

Centralize social media posting logic using Redis Queue (RQ). When player data changes, the scraper enqueues jobs to a persistent worker that handles posting to social platforms.

### Architecture

- **Scraper (cron job):** Enqueues jobs when players are added or status changes occur
- **Worker (always-on):** Processes jobs and posts to social media (currently simulated with 2-second delay)
- **Queue:** Redis stores jobs, enabling multiple team instances to share one worker

### Local setup

**1. Start Redis:**

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**2. Add to `.env`:**

```env
REDIS_URL=redis://localhost:6379
TEAM="Auburn Tigers"
```

**3. Start the worker:**

```bash
uv run rq worker social-posts --url redis://localhost:6379
```

**4. Run the scraper:**

```bash
uv run python -m cfb_tracker.main
```

**5. Monitor the queue:**

```bash
uv run rq info --url redis://localhost:6379
```

### Railway deployment

**1. Provision Redis**

In Railway dashboard:

- Click "New" → "Database" → "Add Redis"
- Railway creates a Redis service with a `REDIS_URL` variable

**2. Update sync service variables**

In your existing cfb-tracker service → Variables tab, add:

| Variable    | Value                               |
| ----------- | ----------------------------------- |
| `TEAM`      | `Auburn Tigers` (or your team name) |
| `REDIS_URL` | Reference: `${{Redis.REDIS_URL}}`   |

**3. Create worker service**

1. Click "New" → "GitHub Repo" → Select `cfb-tracker`
2. In Settings → General:
   - **Service Name:** `cfb-tracker-worker` (or any name)
3. In Settings → Deploy:
   - **Custom Start Command:** `uv run rq worker social-posts --url $REDIS_URL`
4. In Variables tab, add:

| Variable    | Value                             |
| ----------- | --------------------------------- |
| `REDIS_URL` | Reference: `${{Redis.REDIS_URL}}` |

The worker uses the same Docker image as the scraper but with a different start command. The `${{Redis.REDIS_URL}}` reference automatically pulls the connection URL from your Redis service.

### Job payload

Workers receive job payloads like:

```json
{
  "event_type": "status_change",
  "table": "recruits",
  "team": "Auburn Tigers",
  "player": {
    "name": "John Smith",
    "position": "QB",
    "hometown": "Birmingham, AL",
    "stars": 4
  },
  "old_status": "uncommitted",
  "new_status": "committed"
}
```

The worker generates messages like:

- **New recruit:** "🎉 New recruit alert! ⭐⭐⭐⭐ John Smith (QB) from Birmingham, AL..."
- **Commitment:** "🔥 COMMITMENT ALERT! 🔥 John Smith (QB) has committed to Auburn Tigers!"
- **Portal entry:** "📥 Portal update! Mike Johnson (WR) from Alabama is entering the transfer portal..."

### Graceful degradation

If Redis is unavailable, the scraper logs a warning and continues syncing to Supabase without enqueuing jobs. This ensures the core functionality (data sync) is never blocked by social media posting.

## X (Twitter) Posting (optional)

Post player updates to X automatically when the worker processes jobs.

### 1. Create X Developer App

1. Go to [X Developer Portal](https://developer.x.com/en/portal/dashboard)
2. Create a new Project and App
3. In App Settings → User authentication settings:
   - Enable OAuth 1.0a
   - Set App permissions to "Read and Write"
4. In Keys and Tokens, generate:
   - API Key and Secret
   - Access Token and Secret

### 2. Add credentials to `.env`

```env
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

### 3. Railway deployment

Add these variables to your **worker service**:

| Variable                | Value                        |
| ----------------------- | ---------------------------- |
| `X_API_KEY`             | Your X API key               |
| `X_API_SECRET`          | Your X API secret            |
| `X_ACCESS_TOKEN`        | Your X access token          |
| `X_ACCESS_TOKEN_SECRET` | Your X access token secret   |

### Graceful degradation

If X credentials are not configured, the worker continues processing jobs and logs messages without posting to X. This allows testing the full pipeline without a live X account.

## Webhooks (optional)

Send notifications to external services when records are added, updated, or deleted in Supabase.

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

1. **Fetches data** from 247Sports using cfb-cli
2. **Normalizes names** to handle variations:
   - "DJ Smith" and "Derrick Smith" → same player
   - "John Smith Jr." and "John Smith, Jr" → same player
   - "Kensly Ladour-Foustin III" and "Kensley Foustin" → same player
3. **Syncs to Supabase** - upserts new/updated records, deletes players no longer in source data
4. **Enqueues social media jobs** (optional) - when new players are added or status changes, jobs are sent to Redis queue
5. **Worker processes jobs** (optional) - generates and posts social media updates to X
6. **Logs in JSON format** for easy parsing in production

## Project structure

```
src/cfb_tracker/
├── main.py          # Entry point, orchestrates sync
├── config.py        # Environment variable loading
├── normalizer.py    # Name normalization and ID generation
├── fetcher.py       # Fetches data from 247Sports
├── sync.py          # Syncs data to Supabase, enqueues jobs
├── db.py            # Supabase client wrapper
├── queue.py         # Redis queue management
├── worker.py        # Social media job processor
└── twitter.py       # X (Twitter) client and posting
```
