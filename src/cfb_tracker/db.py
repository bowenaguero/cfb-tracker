from supabase import create_client

from cfb_tracker.config import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def get_team_id() -> str:
    """Get the current team_id from config."""
    if not config.TEAM:
        raise ValueError("TEAM environment variable is required")
    return config.TEAM


def get_all_records(table: str) -> list[dict]:
    """Fetch all records for the current team only."""
    team_id = get_team_id()
    response = get_client().table(table).select("*").eq("team_id", team_id).execute()
    return response.data


def upsert_records(table: str, records: list[dict]) -> None:
    """Upsert records with team_id, using composite key for conflict resolution."""
    if not records:
        return
    team_id = get_team_id()
    records_with_team = [{**record, "team_id": team_id} for record in records]
    get_client().table(table).upsert(
        records_with_team, on_conflict="team_id,entry_id"
    ).execute()


def delete_records(table: str, ids: list[str]) -> None:
    """Delete records by entry_id, scoped to current team only."""
    if not ids:
        return
    team_id = get_team_id()
    get_client().table(table).delete().eq("team_id", team_id).in_(
        "entry_id", ids
    ).execute()
