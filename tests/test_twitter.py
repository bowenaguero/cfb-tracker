"""Tests for the twitter module - X posting functionality."""

from unittest.mock import MagicMock, patch

import pytest


class TestInitTwitter:
    """Tests for init_twitter function."""

    def test_init_without_credentials(self, mock_config):
        """Should disable X posting when credentials are missing."""
        mock_config.X_API_KEY = None
        mock_config.X_API_SECRET = None
        mock_config.X_ACCESS_TOKEN = None
        mock_config.X_ACCESS_TOKEN_SECRET = None

        # Need to reimport to reset module state
        from cfb_tracker import twitter as twitter_module

        with patch.object(twitter_module, "config", mock_config):
            # Reset module state
            twitter_module._twitter_enabled = False
            twitter_module._client = None

            result = twitter_module.init_twitter()

        assert result is False
        assert twitter_module.is_enabled() is False

    def test_init_with_partial_credentials(self, mock_config):
        """Should disable X posting when only some credentials are provided."""
        mock_config.X_API_KEY = "key"
        mock_config.X_API_SECRET = None  # Missing
        mock_config.X_ACCESS_TOKEN = "token"  # noqa: S105
        mock_config.X_ACCESS_TOKEN_SECRET = "secret"  # noqa: S105

        from cfb_tracker import twitter as twitter_module

        with patch.object(twitter_module, "config", mock_config):
            twitter_module._twitter_enabled = False
            twitter_module._client = None

            result = twitter_module.init_twitter()

        assert result is False

    def test_init_with_all_credentials(self, mock_config):
        """Should enable X posting when all credentials are provided."""
        mock_config.X_API_KEY = "api_key"
        mock_config.X_API_SECRET = "api_secret"  # noqa: S105
        mock_config.X_ACCESS_TOKEN = "access_token"  # noqa: S105
        mock_config.X_ACCESS_TOKEN_SECRET = "access_token_secret"  # noqa: S105

        from cfb_tracker import twitter as twitter_module

        mock_client = MagicMock()

        with (
            patch.object(twitter_module, "config", mock_config),
            patch.object(twitter_module, "tweepy") as mock_tweepy,
        ):
            mock_tweepy.Client.return_value = mock_client
            twitter_module._twitter_enabled = False
            twitter_module._client = None

            result = twitter_module.init_twitter()

        assert result is True
        mock_tweepy.Client.assert_called_once_with(
            consumer_key="api_key",
            consumer_secret="api_secret",  # noqa: S106
            access_token="access_token",  # noqa: S106
            access_token_secret="access_token_secret",  # noqa: S106
        )

    def test_init_handles_client_exception(self, mock_config):
        """Should disable X posting when client initialization fails."""
        mock_config.X_API_KEY = "api_key"
        mock_config.X_API_SECRET = "api_secret"  # noqa: S105
        mock_config.X_ACCESS_TOKEN = "access_token"  # noqa: S105
        mock_config.X_ACCESS_TOKEN_SECRET = "access_token_secret"  # noqa: S105

        from cfb_tracker import twitter as twitter_module

        with (
            patch.object(twitter_module, "config", mock_config),
            patch.object(twitter_module, "tweepy") as mock_tweepy,
        ):
            mock_tweepy.Client.side_effect = Exception("Auth error")
            twitter_module._twitter_enabled = False
            twitter_module._client = None

            result = twitter_module.init_twitter()

        assert result is False


class TestPostTweet:
    """Tests for post_tweet function."""

    def test_post_tweet_when_disabled(self):
        """Should return None when X posting is disabled."""
        from cfb_tracker import twitter as twitter_module

        twitter_module._twitter_enabled = False
        twitter_module._client = None

        result = twitter_module.post_tweet("Test message")

        assert result is None

    def test_post_tweet_success(self):
        """Should post tweet and return response data."""
        from cfb_tracker import twitter as twitter_module

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "1234567890", "text": "Test message"}
        mock_client.create_tweet.return_value = mock_response

        twitter_module._twitter_enabled = True
        twitter_module._client = mock_client

        result = twitter_module.post_tweet("Test message")

        assert result == {"id": "1234567890", "text": "Test message"}
        mock_client.create_tweet.assert_called_once_with(text="Test message")

    def test_post_tweet_propagates_exception(self):
        """Should propagate exception for retry handling."""
        from cfb_tracker import twitter as twitter_module

        mock_client = MagicMock()
        mock_client.create_tweet.side_effect = Exception("Rate limit exceeded")

        twitter_module._twitter_enabled = True
        twitter_module._client = mock_client

        with pytest.raises(Exception, match="Rate limit exceeded"):
            twitter_module.post_tweet("Test message")


class TestIsEnabled:
    """Tests for is_enabled function."""

    def test_is_enabled_when_disabled(self):
        """Should return False when X posting is disabled."""
        from cfb_tracker import twitter as twitter_module

        twitter_module._twitter_enabled = False

        assert twitter_module.is_enabled() is False

    def test_is_enabled_when_enabled(self):
        """Should return True when X posting is enabled."""
        from cfb_tracker import twitter as twitter_module

        twitter_module._twitter_enabled = True

        assert twitter_module.is_enabled() is True
