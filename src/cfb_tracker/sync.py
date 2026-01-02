import logging
from datetime import datetime, timezone

from cfb_tracker import db
from cfb_tracker.queue import enqueue_event

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

            # Enqueue social post job for new player
            _enqueue_new_player_event(table_name, record)

        elif record.get("status") != existing_record.get("status"):
            # Status changed
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            to_upsert.append(record)

            # Enqueue social post job for status change
            _enqueue_status_change_event(
                table_name,
                record,
                old_status=existing_record.get("status"),
                new_status=record.get("status"),
            )

    if to_upsert:
        db.upsert_records(table_name, to_upsert)

    # Delete records no longer in source
    stale_ids = set(existing_by_id.keys()) - fresh_ids
    if stale_ids:
        # Enqueue player_removed events before deletion
        for stale_id in stale_ids:
            stale_record = existing_by_id[stale_id]
            _enqueue_player_removed_event(table_name, stale_record)
        db.delete_records(table_name, list(stale_ids))

    logger.info(f"[{table_name}] Upserted: {len(to_upsert)}, Deleted: {len(stale_ids)}")
    return {"upserted": len(to_upsert), "deleted": len(stale_ids)}


def _enqueue_new_player_event(table_name: str, record: dict) -> None:
    """Enqueue job for new player event with error handling."""
    try:
        enqueue_event(
            event_type="new_player",
            table=table_name,
            player_data=record,
        )
    except Exception:
        # Log but don't fail the sync
        logger.exception(
            "Failed to enqueue new player event",
            extra={"table": table_name, "player": record.get("name")},
        )


def _enqueue_status_change_event(
    table_name: str,
    record: dict,
    old_status: str | None,
    new_status: str | None,
) -> None:
    """Enqueue job for status change event with error handling."""
    try:
        enqueue_event(
            event_type="status_change",
            table=table_name,
            player_data=record,
            old_status=old_status,
            new_status=new_status,
        )
    except Exception:
        # Log but don't fail the sync
        logger.exception(
            "Failed to enqueue status change event",
            extra={
                "table": table_name,
                "player": record.get("name"),
                "old_status": old_status,
                "new_status": new_status,
            },
        )


def _enqueue_player_removed_event(table_name: str, record: dict) -> None:
    """Enqueue job for player removed event with error handling."""
    try:
        enqueue_event(
            event_type="player_removed",
            table=table_name,
            player_data=record,
        )
    except Exception:
        # Log but don't fail the sync
        logger.exception(
            "Failed to enqueue player removed event",
            extra={"table": table_name, "player": record.get("name")},
        )
