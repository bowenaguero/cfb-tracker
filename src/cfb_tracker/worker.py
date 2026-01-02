import logging
import time

from pythonjsonlogger.json import JsonFormatter

# Set up JSON logging for worker
handler = logging.StreamHandler()
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
handler.setFormatter(formatter)

root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers = [handler]

logger = logging.getLogger(__name__)

# Emoji constants for message types
EMOJI_COMMITTED = "\u2705"  # ✅ checkmark
EMOJI_DECOMMITTED = "\U0001f614"  # 😔 pensive face
EMOJI_SIGNED = "\U0001f4dd"  # 📝 memo
EMOJI_PORTAL_ENTER = "\U0001f6a8"  # 🚨 rotating light
EMOJI_PORTAL_WITHDRAW = "\u21a9\ufe0f"  # ↩️ return arrow


def process_social_post(data: dict) -> dict:
    """
    Process a social media post job for a player event.

    Args:
        data: Job payload containing event details

    Returns:
        dict: Result summary

    Raises:
        Exception: If job processing fails (will be retried by RQ)
    """
    logger.info("Processing social post job", extra={"job_data": data})

    event_type = data.get("event_type")
    table = data.get("table")
    team = data.get("team")
    player = data.get("player", {})

    # Validate required fields
    if not all([event_type, table, team, player.get("name")]):
        error_msg = "Missing required fields in job payload"
        logger.error(error_msg, extra={"job_data": data})
        raise ValueError(error_msg)

    # Build human-readable message based on event type
    message = _build_message(event_type, table, team, player, data)

    logger.info("Social post message generated", extra={"post_content": message, "player_name": player.get("name")})

    # Simulate social media API call (2-second sleep)
    # In production, this would be replaced with actual API calls to Twitter/BlueSky/etc.
    time.sleep(2)

    logger.info(
        "Social post job completed",
        extra={
            "event_type": event_type,
            "player_name": player.get("name"),
            "table": table,
        },
    )

    return {
        "success": True,
        "message": message,
        "player": player.get("name"),
        "event_type": event_type,
    }


def _format_stars(stars: int | None) -> str:
    """Format stars as repeated star emojis."""
    if not stars or stars < 1:
        return ""
    return "\u2b50" * stars


def _format_url_line(player_url: str | None) -> str:
    """Format player URL as trailing line, or empty string if not available."""
    if player_url:
        return f"\n\n{player_url}"
    return ""


def _build_message(  # noqa: C901
    event_type: str,
    table: str,
    team: str,
    player: dict,
    data: dict,
) -> str:
    """Build human-readable social media message based on event type and table."""

    name = player.get("name")
    position = player.get("position")
    player_url = player.get("player_url")
    status = data.get("status") or data.get("new_status", "")
    status_lower = status.lower() if status else ""

    # RECRUITING MESSAGES (table="recruits")
    if table == "recruits":
        stars = _format_stars(player.get("stars"))
        url_line = _format_url_line(player_url)

        # Check status for both new_player and status_change events
        if status_lower == "committed":
            return f"{EMOJI_COMMITTED}\n{name}, {stars} {position}, has committed to the {team}{url_line}"

        elif status_lower == "decommitted":
            return f"{EMOJI_DECOMMITTED}\n{name}, {stars} {position}, has decommitted from the {team}{url_line}"

        elif status_lower in ("signed", "enrolled"):
            # Signed messages don't include URL per requirements
            return f"{EMOJI_SIGNED}\n{name}, {stars} {position}, has signed with the {team}"

    # PORTAL MESSAGES (table="portal")
    elif table == "portal":
        direction = player.get("direction")
        source_school = player.get("source_school", "")
        url_line = _format_url_line(player_url)

        # OUTGOING DIRECTION
        if direction == "outgoing":
            # Entered portal (new_player with direction="outgoing")
            if event_type == "new_player":
                return f"{EMOJI_PORTAL_ENTER}\n{team} {position} {name} has entered the transfer portal{url_line}"

            # Withdrawn from portal (player_removed with direction="outgoing")
            elif event_type == "player_removed":
                return f"{EMOJI_PORTAL_WITHDRAW}\n{team} {position} {name} has withdrawn from the transfer portal{url_line}"

        # INCOMING DIRECTION
        elif direction == "incoming":
            # Signed (status = "signed" or "enrolled")
            if status_lower in ("signed", "enrolled"):
                # Signed messages don't include URL per requirements
                return f"{EMOJI_SIGNED}\n{source_school} {position} {name} has signed with the {team}"

            # Committed (new_player with direction="incoming")
            elif event_type == "new_player":
                return f"{EMOJI_COMMITTED}\n{source_school} {position} {name} has committed to the {team}{url_line}"

            # Decommitted (player_removed with direction="incoming")
            elif event_type == "player_removed":
                return (
                    f"{EMOJI_DECOMMITTED}\n{source_school} {position} {name} has decommitted from the {team}{url_line}"
                )

    # Fallback for unhandled cases
    return f"Player update: {name} ({position}) - {team}"
