"""Tests for the queue module - Redis queue management."""

from unittest.mock import MagicMock, patch

import pytest

from cfb_tracker import queue as queue_module


@pytest.fixture(autouse=True)
def reset_queue_state():
    """Reset queue module state before each test."""
    queue_module._queue = None
    queue_module._redis_available = False
    yield
    queue_module._queue = None
    queue_module._redis_available = False


class TestInitQueue:
    """Tests for init_queue function."""

    def test_init_without_redis_url(self, mock_config):
        """Should return False when REDIS_URL is not configured."""
        mock_config.REDIS_URL = None

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.init_queue()

        assert result is False
        assert queue_module._redis_available is False

    def test_init_with_valid_redis(self, mock_config):
        """Should return True when Redis connection succeeds."""
        mock_redis_conn = MagicMock()
        mock_redis_conn.ping.return_value = True

        with (
            patch.object(queue_module, "config", mock_config),
            patch.object(queue_module, "Redis") as mock_redis_cls,
            patch.object(queue_module, "Queue") as mock_queue_cls,
        ):
            mock_redis_cls.from_url.return_value = mock_redis_conn

            result = queue_module.init_queue()

        assert result is True
        assert queue_module._redis_available is True
        mock_redis_cls.from_url.assert_called_once_with(mock_config.REDIS_URL, socket_connect_timeout=5)
        mock_queue_cls.assert_called_once_with("social-posts", connection=mock_redis_conn)

    def test_init_with_redis_connection_error(self, mock_config):
        """Should return False when Redis connection fails."""
        from redis.exceptions import ConnectionError as RedisConnectionError

        with (
            patch.object(queue_module, "config", mock_config),
            patch.object(queue_module, "Redis") as mock_redis_cls,
        ):
            mock_redis_cls.from_url.side_effect = RedisConnectionError("Connection refused")

            result = queue_module.init_queue()

        assert result is False
        assert queue_module._redis_available is False


class TestEnqueueEvent:
    """Tests for enqueue_event function."""

    def test_enqueue_skipped_when_redis_not_available(self, sample_recruit, mock_config):
        """Should return False when Redis is not available."""
        queue_module._redis_available = False

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="new_player",
                table="recruits",
                player_data=sample_recruit,
            )

        assert result is False

    def test_enqueue_new_player_recruits(self, sample_recruit, mock_config):
        """Should enqueue new player event for recruits table."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="new_player",
                table="recruits",
                player_data=sample_recruit,
            )

        assert result is True
        mock_queue.enqueue.assert_called_once()

        # Verify payload structure
        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert payload["event_type"] == "new_player"
        assert payload["table"] == "recruits"
        assert payload["team"] == mock_config.TEAM
        assert payload["player"]["name"] == sample_recruit["name"]
        assert payload["player"]["position"] == sample_recruit["position"]
        assert payload["player"]["player_url"] == sample_recruit["player_url"]
        assert payload["player"]["stars"] == sample_recruit["stars"]
        assert payload["player"]["hometown"] == sample_recruit["hometown"]
        assert payload["status"] == sample_recruit["status"]

    def test_enqueue_status_change_recruits(self, sample_recruit, mock_config):
        """Should enqueue status change event with old and new status."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="status_change",
                table="recruits",
                player_data=sample_recruit,
                old_status="uncommitted",
                new_status="committed",
            )

        assert result is True

        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert payload["event_type"] == "status_change"
        assert payload["old_status"] == "uncommitted"
        assert payload["new_status"] == "committed"

    def test_enqueue_new_player_portal(self, sample_portal_incoming, mock_config):
        """Should enqueue new player event for portal table with direction."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="new_player",
                table="portal",
                player_data=sample_portal_incoming,
            )

        assert result is True

        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert payload["event_type"] == "new_player"
        assert payload["table"] == "portal"
        assert payload["player"]["direction"] == "incoming"
        assert payload["player"]["source_school"] == "Alabama"

    def test_enqueue_player_removed(self, sample_portal_outgoing, mock_config):
        """Should enqueue player_removed event."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="player_removed",
                table="portal",
                player_data=sample_portal_outgoing,
            )

        assert result is True

        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert payload["event_type"] == "player_removed"
        assert payload["table"] == "portal"
        assert payload["player"]["direction"] == "outgoing"

    def test_enqueue_handles_exception(self, sample_recruit, mock_config):
        """Should return False and log exception when enqueue fails."""
        mock_queue = MagicMock()
        mock_queue.enqueue.side_effect = Exception("Queue error")

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="new_player",
                table="recruits",
                player_data=sample_recruit,
            )

        assert result is False

    def test_enqueue_includes_player_url(self, sample_recruit, mock_config):
        """Should include player_url in the payload."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            queue_module.enqueue_event(
                event_type="new_player",
                table="recruits",
                player_data=sample_recruit,
            )

        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert "player_url" in payload["player"]
        assert payload["player"]["player_url"] == sample_recruit["player_url"]

    def test_enqueue_handles_missing_player_url(self, sample_recruit_no_url, mock_config):
        """Should handle None player_url gracefully."""
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_queue.enqueue.return_value = mock_job

        queue_module._redis_available = True
        queue_module._queue = mock_queue

        with patch.object(queue_module, "config", mock_config):
            result = queue_module.enqueue_event(
                event_type="new_player",
                table="recruits",
                player_data=sample_recruit_no_url,
            )

        assert result is True

        call_args = mock_queue.enqueue.call_args
        payload = call_args[0][1]

        assert payload["player"]["player_url"] is None
