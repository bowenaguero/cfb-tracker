from supabase import create_client

from cfb_tracker.config import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def get_all_records(table: str) -> list[dict]:
    response = get_client().table(table).select("*").execute()
    return response.data


def upsert_records(table: str, records: list[dict]) -> None:
    if not records:
        return
    get_client().table(table).upsert(records, on_conflict="entry_id").execute()


def delete_records(table: str, ids: list[str]) -> None:
    if not ids:
        return
    get_client().table(table).delete().in_("entry_id", ids).execute()
