"""X (Twitter) client and posting functionality."""

import logging

import tweepy

from cfb_tracker.config import config

logger = logging.getLogger(__name__)

_client: tweepy.Client | None = None
_twitter_enabled = False


def init_twitter() -> bool:
    """
    Initialize X client if credentials are configured.

    Returns:
        bool: True if X client initialized successfully, False otherwise
    """
    global _client, _twitter_enabled

    # Check if all credentials are provided
    if not all([
        config.X_API_KEY,
        config.X_API_SECRET,
        config.X_ACCESS_TOKEN,
        config.X_ACCESS_TOKEN_SECRET,
    ]):
        logger.info("X credentials not configured - posting disabled")
        _twitter_enabled = False
        return False

    try:
        _client = tweepy.Client(
            consumer_key=config.X_API_KEY,
            consumer_secret=config.X_API_SECRET,
            access_token=config.X_ACCESS_TOKEN,
            access_token_secret=config.X_ACCESS_TOKEN_SECRET,
        )
        _twitter_enabled = True
        logger.info("X client initialized successfully")
    except Exception:
        logger.exception("Failed to initialize X client")
        _twitter_enabled = False
        return False
    else:
        return True


def post_tweet(message: str) -> dict | None:
    """
    Post a tweet to X.

    Args:
        message: The tweet text to post (max 280 characters)

    Returns:
        dict: Response data containing tweet ID if successful, None if disabled

    Raises:
        tweepy.TweepyException: If the API request fails (for retry handling)
    """
    if not _twitter_enabled or _client is None:
        logger.debug("X posting disabled - skipping tweet")
        return None

    response = _client.create_tweet(text=message)
    return response.data


def is_enabled() -> bool:
    """Check if X posting is enabled."""
    return _twitter_enabled
