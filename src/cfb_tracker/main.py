import logging

from cfb_tracker.config import config
from cfb_tracker.fetcher import fetch_portal, fetch_recruits
from cfb_tracker.sync import sync_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting CFB Tracker sync...")

    recruits = fetch_recruits()
    if recruits:
        sync_table(config.RECRUITS_TABLE, recruits)
    else:
        logger.warning("No recruit data fetched from any source")

    portal = fetch_portal()
    if portal:
        sync_table(config.PORTAL_TABLE, portal)
    else:
        logger.warning("No portal data fetched from any source")

    logger.info("Sync complete")


if __name__ == "__main__":
    main()
