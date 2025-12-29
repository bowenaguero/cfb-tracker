import logging

from cfb_tracker import db

logger = logging.getLogger(__name__)


def sync_table(table_name: str, fresh_records: list[dict]) -> dict:
    existing = db.get_all_records(table_name)
    existing_ids = {r["entry_id"] for r in existing}
    fresh_ids = {r["entry_id"] for r in fresh_records}

    db.upsert_records(table_name, fresh_records)
    upserted = len(fresh_records)

    stale_ids = existing_ids - fresh_ids
    if stale_ids:
        db.delete_records(table_name, list(stale_ids))

    logger.info(f"[{table_name}] Upserted: {upserted}, Deleted: {len(stale_ids)}")
    return {"upserted": upserted, "deleted": len(stale_ids)}
