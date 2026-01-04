import logging

from cfb_cli import get_scraper

from cfb_tracker.config import config
from cfb_tracker.normalizer import generate_id, normalize_position

logger = logging.getLogger(__name__)


def _recruit_to_dict(recruit) -> dict:
    return {
        "entry_id": generate_id(recruit.name),
        "name": recruit.name.strip(),
        "position": normalize_position(recruit.position),
        "hometown": recruit.hometown,
        "stars": recruit.stars,
        "rating": recruit.rating,
        "status": getattr(recruit, "status", None),
        "source": "247sports",
        "player_url": getattr(recruit, "player_url", None),
    }


def _portal_to_dict(player, direction: str) -> dict:
    return {
        "entry_id": generate_id(player.name),
        "name": player.name.strip(),
        "position": normalize_position(player.position),
        "direction": direction,
        "source_school": getattr(player, "source_school", None),
        "status": getattr(player, "status", None),
        "source": "247sports",
        "player_url": getattr(player, "player_url", None),
    }


def fetch_recruits() -> list[dict]:
    """Fetch recruit data from 247Sports."""
    try:
        scraper = get_scraper("247sports", headless=True)
        data = scraper.fetch_recruit_data(config.TEAM_247_NAME, config.TEAM_247_YEAR)
        records = [_recruit_to_dict(r) for r in data.recruits]
        logger.info(f"Fetched {len(records)} recruits from 247Sports")
    except Exception:
        logger.exception("Failed to fetch recruits from 247Sports")
        return []
    else:
        return records


def fetch_portal() -> list[dict]:
    """Fetch transfer portal data from 247Sports."""
    try:
        scraper = get_scraper("247sports", headless=True)
        data = scraper.fetch_portal_data(config.TEAM_247_NAME, config.TEAM_247_YEAR)
        records = []
        for p in data.incoming:
            records.append(_portal_to_dict(p, "incoming"))
        for p in data.outgoing:
            records.append(_portal_to_dict(p, "outgoing"))
        logger.info(f"Fetched {len(data.incoming)} incoming, {len(data.outgoing)} outgoing from 247Sports")
    except Exception:
        logger.exception("Failed to fetch portal from 247Sports")
        return []
    else:
        return records
