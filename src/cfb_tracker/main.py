import logging

from pythonjsonlogger import jsonlogger

from cfb_tracker.config import config
from cfb_tracker.fetcher import fetch_portal, fetch_recruits
from cfb_tracker.queue import init_queue
from cfb_tracker.sync import sync_table


def setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


setup_logging()
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting CFB Tracker sync")

    # Initialize Redis queue (graceful if unavailable)
    queue_available = init_queue()
    if queue_available:
        logger.info("Queue initialized - social posts will be enqueued")
    else:
        logger.info("Queue unavailable - sync will continue without social posts")

    recruits = fetch_recruits()
    if recruits:
        result = sync_table(config.RECRUITS_TABLE, recruits)
        logger.info("Recruits sync complete", extra={"table": config.RECRUITS_TABLE, **result})
    else:
        logger.warning("No recruit data fetched from any source")

    portal = fetch_portal()
    if portal:
        result = sync_table(config.PORTAL_TABLE, portal)
        logger.info("Portal sync complete", extra={"table": config.PORTAL_TABLE, **result})
    else:
        logger.warning("No portal data fetched from any source")

    logger.info("Sync complete")


if __name__ == "__main__":
    main()
