import logging

from cfb_cli import get_scraper

from cfb_tracker.config import config
from cfb_tracker.normalizer import generate_id, normalize_position

logger = logging.getLogger(__name__)


def _recruit_to_dict(recruit, source: str) -> dict:
    return {
        "entry_id": generate_id(recruit.name),
        "name": recruit.name.strip(),
        "position": normalize_position(recruit.position),
        "hometown": recruit.hometown,
        "stars": recruit.stars,
        "rating": recruit.rating,
        "status": getattr(recruit, "status", None),
        "player_url": getattr(recruit, "url", None) or getattr(recruit, "profile_url", None),
        "source": source,
    }


def _portal_to_dict(player, direction: str, source: str) -> dict:
    return {
        "entry_id": generate_id(player.name),
        "name": player.name.strip(),
        "position": normalize_position(player.position),
        "direction": direction,
        "source_school": getattr(player, "source_school", None),
        "status": getattr(player, "status", None),
        "player_url": getattr(player, "url", None) or getattr(player, "profile_url", None),
        "source": source,
    }


def _merge_records(records: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for record in records:
        rid = record["entry_id"]
        if rid not in merged:
            merged[rid] = record
        else:
            existing = merged[rid]
            is_247 = record["source"] == "247"

            # 247 is authoritative - prefer its data for all fields
            if is_247:
                for key in [
                    "stars",
                    "rating",
                    "status",
                    "position",
                    "hometown",
                    "direction",
                    "source_school",
                    "player_url",
                ]:
                    if record.get(key) is not None:
                        existing[key] = record[key]
            else:
                # on3 only fills gaps where 247 has no data
                for key in [
                    "stars",
                    "rating",
                    "status",
                    "position",
                    "hometown",
                    "direction",
                    "source_school",
                    "player_url",
                ]:
                    if existing.get(key) is None and record.get(key) is not None:
                        existing[key] = record[key]

            # track both sources
            sources = set(existing["source"].split(","))
            sources.add(record["source"])
            existing["source"] = ",".join(sorted(sources))
    return list(merged.values())


def fetch_recruits() -> list[dict]:
    records = []

    try:
        scraper = get_scraper("on3", headless=True)
        data = scraper.fetch_recruit_data(config.ON3_TEAM_NAME, config.ON3_YEAR)
        for r in data.recruits:
            records.append(_recruit_to_dict(r, "on3"))
        logger.info(f"Fetched {len(data.recruits)} recruits from On3")
    except Exception:
        logger.exception("Failed to fetch from On3")

    try:
        scraper = get_scraper("247sports", headless=True)
        data = scraper.fetch_recruit_data(config.TEAM_247_NAME, config.TEAM_247_YEAR)
        for r in data.recruits:
            records.append(_recruit_to_dict(r, "247"))
        logger.info(f"Fetched {len(data.recruits)} recruits from 247Sports")
    except Exception:
        logger.exception("Failed to fetch from 247Sports")

    return _merge_records(records)


def fetch_portal() -> list[dict]:
    records = []

    try:
        scraper = get_scraper("on3", headless=True)
        data = scraper.fetch_portal_data(config.ON3_TEAM_NAME, config.ON3_YEAR)
        for p in data.incoming:
            records.append(_portal_to_dict(p, "incoming", "on3"))
        for p in data.outgoing:
            records.append(_portal_to_dict(p, "outgoing", "on3"))
        logger.info(f"Fetched {len(data.incoming)} incoming, {len(data.outgoing)} outgoing from On3")
    except Exception:
        logger.exception("Failed to fetch portal from On3")

    try:
        scraper = get_scraper("247sports", headless=True)
        data = scraper.fetch_portal_data(config.TEAM_247_NAME, config.TEAM_247_YEAR)
        for p in data.incoming:
            records.append(_portal_to_dict(p, "incoming", "247"))
        for p in data.outgoing:
            records.append(_portal_to_dict(p, "outgoing", "247"))
        logger.info(f"Fetched {len(data.incoming)} incoming, {len(data.outgoing)} outgoing from 247Sports")
    except Exception:
        logger.exception("Failed to fetch portal from 247Sports")

    return _merge_records(records)
