import logging
from datetime import datetime, timezone

from cfb_tracker import db

logger = logging.getLogger(__name__)


def sync_table(table_name: str, fresh_records: list[dict]) -> dict:
    existing = db.get_all_records(table_name)
    existing_by_id = {r["entry_id"]: r for r in existing}
    fresh_ids = {r["entry_id"] for r in fresh_records}

    # Only upsert records where status changed or record is new
    to_upsert = []
    for record in fresh_records:
        entry_id = record["entry_id"]
        existing_record = existing_by_id.get(entry_id)

        if existing_record is None:
            # New record
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            to_upsert.append(record)
        elif record.get("status") != existing_record.get("status"):
            # Status changed
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            to_upsert.append(record)

    if to_upsert:
        db.upsert_records(table_name, to_upsert)

    # Delete records no longer in source
    stale_ids = set(existing_by_id.keys()) - fresh_ids
    if stale_ids:
        db.delete_records(table_name, list(stale_ids))

    logger.info(f"[{table_name}] Upserted: {len(to_upsert)}, Deleted: {len(stale_ids)}")
    return {"upserted": len(to_upsert), "deleted": len(stale_ids)}
