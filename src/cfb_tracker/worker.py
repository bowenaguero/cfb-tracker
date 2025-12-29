import logging
import time

from pythonjsonlogger import jsonlogger

# Set up JSON logging for worker
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
handler.setFormatter(formatter)

root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers = [handler]

logger = logging.getLogger(__name__)


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

    logger.info("Social post message generated", extra={"message": message, "player": player.get("name")})

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


def _build_message(
    event_type: str,
    table: str,
    team: str,
    player: dict,
    data: dict,
) -> str:
    """Build human-readable social media message."""

    name = player.get("name")
    position = player.get("position")

    if event_type == "new_player":
        if table == "recruits":
            stars = player.get("stars")
            hometown = player.get("hometown")
            star_emoji = "⭐" * stars if stars else ""
            return f"🎉 New recruit alert! {star_emoji}\n{name} ({position}) from {hometown} is being tracked for {team}!"

        elif table == "portal":
            direction = player.get("direction")
            source_school = player.get("source_school")
            direction_emoji = "📥" if direction == "incoming" else "📤"

            if direction == "incoming":
                if source_school:
                    return f"{direction_emoji} Portal update!\n{name} ({position}) from {source_school} is entering the transfer portal for {team}!"
                else:
                    return f"{direction_emoji} Portal update!\n{name} ({position}) is entering the transfer portal for {team}!"
            else:
                return f"{direction_emoji} Portal update!\n{name} ({position}) is leaving {team} for the transfer portal"

    elif event_type == "status_change":
        old_status = data.get("old_status")
        new_status = data.get("new_status")

        if table == "recruits":
            if new_status == "committed":
                return f"🔥 COMMITMENT ALERT! 🔥\n{name} ({position}) has committed to {team}!"
            elif new_status == "decommitted":
                return f"❌ Decommitment\n{name} ({position}) has decommitted from {team}"
            else:
                return f"📝 Status update for {name} ({position}): {old_status} → {new_status}"

        elif table == "portal":
            direction = player.get("direction")
            source_school = player.get("source_school")

            if direction == "incoming" and new_status == "committed":
                if source_school:
                    return f"🎯 Transfer commitment!\n{name} ({position}) from {source_school} has committed to {team} via the transfer portal!"
                else:
                    return f"🎯 Transfer commitment!\n{name} ({position}) has committed to {team} via the transfer portal!"
            else:
                return f"📝 Portal status update for {name} ({position}): {old_status} → {new_status}"

    # Fallback
    return f"Player update: {name} ({position}) - {team}"
