"""Shared test fixtures and mocks for cfb-tracker tests."""

import os

# Set required environment variables BEFORE importing any cfb_tracker modules
# This is necessary because config.py loads settings at module import time
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-service-role-key")
os.environ.setdefault("TEAM_247_NAME", "test")
os.environ.setdefault("TEAM_247_YEAR", "2026")
os.environ.setdefault("TEAM", "Test Tigers")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from unittest.mock import MagicMock, patch

import pytest
from cfb_cli import Player, Recruit, RecruitData, RecruitStatus, TransferPortalData, TransferStatus

# ============================================================================
# Mock Config
# ============================================================================


@pytest.fixture
def mock_config():
    """Mock configuration object with test values."""
    config = MagicMock()
    config.SUPABASE_URL = "https://test.supabase.co"
    config.SUPABASE_KEY = "test-key"
    config.RECRUITS_TABLE = "recruits"
    config.PORTAL_TABLE = "portal"
    config.TEAM_247_NAME = "test"
    config.TEAM_247_YEAR = 2026
    config.REDIS_URL = "redis://localhost:6379"
    config.TEAM = "Test Tigers"
    return config


# ============================================================================
# Sample Player Data (dict format - as stored in database)
# ============================================================================


@pytest.fixture
def sample_recruit():
    """Sample recruit record (dict format)."""
    return {
        "entry_id": "abc123",
        "name": "John Smith",
        "position": "QB",
        "hometown": "Birmingham, AL",
        "stars": 4,
        "rating": 0.9500,
        "status": "committed",
        "player_url": "https://247sports.com/player/john-smith",
    }


@pytest.fixture
def sample_recruit_no_url():
    """Sample recruit record without player URL (dict format)."""
    return {
        "entry_id": "def456",
        "name": "Mike Johnson",
        "position": "WR",
        "hometown": "Atlanta, GA",
        "stars": 3,
        "rating": 0.8800,
        "status": "uncommitted",
        "player_url": None,
    }


@pytest.fixture
def sample_portal_incoming():
    """Sample incoming portal player (dict format)."""
    return {
        "entry_id": "ghi789",
        "name": "Alex Williams",
        "position": "RB",
        "direction": "incoming",
        "source_school": "Alabama",
        "status": "committed",
        "player_url": "https://247sports.com/player/alex-williams",
    }


@pytest.fixture
def sample_portal_outgoing():
    """Sample outgoing portal player (dict format)."""
    return {
        "entry_id": "jkl012",
        "name": "Chris Davis",
        "position": "LB",
        "direction": "outgoing",
        "source_school": None,
        "status": None,
        "player_url": "https://247sports.com/player/chris-davis",
    }


# ============================================================================
# cfb-cli Objects (using real models)
# ============================================================================


@pytest.fixture
def cfb_recruit():
    """Real cfb-cli Recruit object."""
    return Recruit(
        name="John Smith",
        position="Quarterback",
        hometown="Birmingham, AL",
        stars=4,
        rating=0.95,
        status=RecruitStatus.COMMITTED,
        player_url="https://247sports.com/player/john-smith",
    )


@pytest.fixture
def cfb_recruit_no_url():
    """Real cfb-cli Recruit object without URL."""
    return Recruit(
        name="Mike Johnson",
        position="Wide Receiver",
        hometown="Atlanta, GA",
        stars=3,
        rating=0.88,
        status=None,  # No status yet
        player_url=None,
    )


@pytest.fixture
def cfb_portal_player_incoming():
    """Real cfb-cli Player object (incoming transfer)."""
    return Player(
        name="Alex Williams",
        position="Running Back",
        source_school="Alabama",
        status=TransferStatus.COMMITTED,
        player_url="https://247sports.com/player/alex-williams",
    )


@pytest.fixture
def cfb_portal_player_outgoing():
    """Real cfb-cli Player object (outgoing transfer)."""
    return Player(
        name="Chris Davis",
        position="Linebacker",
        source_school=None,
        status=TransferStatus.ENTERED,
        player_url="https://247sports.com/player/chris-davis",
    )


@pytest.fixture
def cfb_recruit_data(cfb_recruit, cfb_recruit_no_url):
    """Real cfb-cli RecruitData object."""
    return RecruitData(
        team="Test Tigers",
        year=2026,
        recruits=[cfb_recruit, cfb_recruit_no_url],
    )


@pytest.fixture
def cfb_portal_data(cfb_portal_player_incoming, cfb_portal_player_outgoing):
    """Real cfb-cli TransferPortalData object."""
    return TransferPortalData(
        team="Test Tigers",
        year=2026,
        incoming=[cfb_portal_player_incoming],
        outgoing=[cfb_portal_player_outgoing],
    )


# ============================================================================
# Mock Database
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock database module."""
    with patch("cfb_tracker.sync.db") as mock:
        mock.get_all_records.return_value = []
        mock.upsert_records.return_value = None
        mock.delete_records.return_value = None
        yield mock


# ============================================================================
# Mock Redis/Queue
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch("cfb_tracker.queue.Redis") as mock_redis_cls:
        mock_conn = MagicMock()
        mock_conn.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_conn
        yield mock_conn


@pytest.fixture
def mock_queue():
    """Mock RQ Queue."""
    with patch("cfb_tracker.queue.Queue") as mock_queue_cls:
        mock_q = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "test-job-123"
        mock_q.enqueue.return_value = mock_job
        mock_queue_cls.return_value = mock_q
        yield mock_q
