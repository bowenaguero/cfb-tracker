import logging
from typing import Literal

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue, Retry

from cfb_tracker.config import config

logger = logging.getLogger(__name__)

_queue: Queue | None = None
_redis_available = False


def init_queue() -> bool:
    """
    Initialize Redis connection and queue.

    Returns:
        bool: True if Redis is available and queue initialized, False otherwise
    """
    global _queue, _redis_available

    if not config.REDIS_URL:
        logger.warning("REDIS_URL not configured - social post jobs will be skipped")
        _redis_available = False
        return False

    try:
        redis_conn = Redis.from_url(config.REDIS_URL, socket_connect_timeout=5)
        # Test connection
        redis_conn.ping()

        _queue = Queue("social-posts", connection=redis_conn)
        _redis_available = True

        logger.info(
            "Redis queue initialized successfully", extra={"queue": "social-posts"}
        )

    except RedisConnectionError as e:
        logger.warning(
            "Failed to connect to Redis - social post jobs will be skipped",
            extra={"error": str(e)},
        )
        _redis_available = False
        return False
    except Exception:
        logger.exception("Unexpected error initializing Redis queue")
        _redis_available = False
        return False
    else:
        return True


def enqueue_event(
    event_type: Literal["new_player", "status_change", "player_removed"],
    table: Literal["recruits", "portal"],
    player_data: dict,
    old_status: str | None = None,
    new_status: str | None = None,
) -> bool:
    """
    Enqueue a player event for social media posting.

    Args:
        event_type: Type of event ("new_player" or "status_change")
        table: Table name ("recruits" or "portal")
        player_data: Player record data
        old_status: Previous status (for status_change events)
        new_status: New status (for status_change events)

    Returns:
        bool: True if job was enqueued successfully, False otherwise
    """
    if not _redis_available or _queue is None:
        logger.debug("Redis not available - skipping job enqueue")
        return False

    try:
        # Build job payload
        payload = {
            "event_type": event_type,
            "table": table,
            "team": config.TEAM,
            "player": {
                "name": player_data.get("name"),
                "position": player_data.get("position"),
                "entry_id": player_data.get("entry_id"),
                "player_url": player_data.get("player_url"),
            },
        }

        # Add recruit-specific fields
        if table == "recruits":
            payload["player"]["hometown"] = player_data.get("hometown")
            payload["player"]["stars"] = player_data.get("stars")
            payload["player"]["rating"] = player_data.get("rating")

        # Add portal-specific fields
        if table == "portal":
            payload["player"]["direction"] = player_data.get("direction")
            payload["player"]["source_school"] = player_data.get("source_school")

        # Add status information
        if event_type == "status_change":
            payload["old_status"] = old_status
            payload["new_status"] = new_status
        elif event_type == "new_player":
            payload["status"] = player_data.get("status")

        # Enqueue the job
        job = _queue.enqueue(
            "cfb_worker.worker.process_social_post",
            payload,
            job_timeout="5m",
            result_ttl=3600,  # Keep results for 1 hour
            failure_ttl=86400,  # Keep failures for 24 hours
            retry=Retry(max=3, interval=[60, 300, 900]),  # Retry at 1min, 5min, 15min
        )

        logger.info(
            "Enqueued social post job",
            extra={
                "job_id": job.id,
                "event_type": event_type,
                "player_name": player_data.get("name"),
                "table": table,
            },
        )

    except Exception:
        logger.exception(
            "Failed to enqueue social post job",
            extra={
                "event_type": event_type,
                "player_name": player_data.get("name"),
            },
        )
        return False
    else:
        return True
