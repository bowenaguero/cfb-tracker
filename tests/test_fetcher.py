"""Tests for the fetcher module - data fetching and transformation."""

from unittest.mock import MagicMock, patch

from cfb_cli import Player, Recruit, RecruitStatus, TransferStatus

from cfb_tracker import fetcher as fetcher_module
from cfb_tracker.fetcher import (
    _portal_to_dict,
    _recruit_to_dict,
)


class TestRecruitToDict:
    """Tests for _recruit_to_dict function."""

    def test_converts_all_fields(self, cfb_recruit):
        """Should convert recruit object to dictionary with all fields."""
        result = _recruit_to_dict(cfb_recruit)

        assert result["name"] == "John Smith"
        assert result["position"] == "qb"  # Normalized from "Quarterback"
        assert result["hometown"] == "Birmingham, AL"
        assert result["stars"] == 4
        assert result["rating"] == 0.95
        assert result["status"] == RecruitStatus.COMMITTED
        assert result["player_url"] == "https://247sports.com/player/john-smith"
        assert "entry_id" in result  # Generated hash

    def test_normalizes_position(self):
        """Should normalize position to abbreviation."""
        recruit = Recruit(
            name="Test Player",
            position="Wide Receiver",
            hometown="Test City",
            stars=3,
            rating=0.85,
        )

        result = _recruit_to_dict(recruit)

        assert result["position"] == "wr"

    def test_strips_name_whitespace(self):
        """Should strip whitespace from name."""
        recruit = Recruit(
            name="  John Smith  ",
            position="QB",
            hometown="Test City",
            stars=3,
            rating=0.85,
        )

        result = _recruit_to_dict(recruit)

        assert result["name"] == "John Smith"

    def test_handles_none_status(self):
        """Should handle recruits with None status."""
        recruit = Recruit(
            name="John Smith",
            position="QB",
            hometown="Test City",
            stars=3,
            rating=0.85,
            status=None,
        )

        result = _recruit_to_dict(recruit)

        assert result["status"] is None

    def test_handles_none_url(self, cfb_recruit_no_url):
        """Should handle recruits without player URL."""
        result = _recruit_to_dict(cfb_recruit_no_url)

        assert result["player_url"] is None

    def test_generates_consistent_entry_id(self):
        """Should generate consistent entry_id for same name."""
        recruit1 = Recruit(name="John Smith", position="QB", hometown="City A", stars=4, rating=0.9)
        recruit2 = Recruit(name="John Smith", position="WR", hometown="City B", stars=3, rating=0.8)

        result1 = _recruit_to_dict(recruit1)
        result2 = _recruit_to_dict(recruit2)

        assert result1["entry_id"] == result2["entry_id"]


class TestPortalToDict:
    """Tests for _portal_to_dict function."""

    def test_converts_incoming_player(self, cfb_portal_player_incoming):
        """Should convert incoming portal player to dictionary."""
        result = _portal_to_dict(cfb_portal_player_incoming, "incoming")

        assert result["name"] == "Alex Williams"
        assert result["position"] == "rb"  # Normalized from "Running Back"
        assert result["direction"] == "incoming"
        assert result["source_school"] == "Alabama"
        assert result["status"] == TransferStatus.COMMITTED
        assert result["player_url"] == "https://247sports.com/player/alex-williams"

    def test_converts_outgoing_player(self, cfb_portal_player_outgoing):
        """Should convert outgoing portal player to dictionary."""
        result = _portal_to_dict(cfb_portal_player_outgoing, "outgoing")

        assert result["direction"] == "outgoing"
        assert result["source_school"] is None
        assert result["status"] == TransferStatus.ENTERED
        assert result["player_url"] == "https://247sports.com/player/chris-davis"

    def test_handles_none_attributes(self):
        """Should handle players with None optional attributes."""
        player = Player(
            name="Test Player",
            position="QB",
            source_school=None,
            status=None,
            player_url=None,
        )

        result = _portal_to_dict(player, "incoming")

        assert result["source_school"] is None
        assert result["status"] is None
        assert result["player_url"] is None


class TestFetchRecruits:
    """Tests for fetch_recruits function."""

    def test_fetches_from_247(self, mock_config, cfb_recruit_data):
        """Should fetch recruits from 247Sports."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_recruit_data.return_value = cfb_recruit_data

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", return_value=mock_scraper),
        ):
            result = fetcher_module.fetch_recruits()

        assert len(result) == 2
        mock_scraper.fetch_recruit_data.assert_called_once_with(
            mock_config.TEAM_247_NAME,
            mock_config.TEAM_247_YEAR,
        )

    def test_handles_fetch_failure(self, mock_config):
        """Should return empty list on fetch failure."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_recruit_data.side_effect = Exception("Fetch error")

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", return_value=mock_scraper),
        ):
            result = fetcher_module.fetch_recruits()

        assert result == []


class TestFetchPortal:
    """Tests for fetch_portal function."""

    def test_fetches_incoming_and_outgoing(self, mock_config, cfb_portal_data):
        """Should fetch both incoming and outgoing portal players."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_portal_data.return_value = cfb_portal_data

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", return_value=mock_scraper),
        ):
            result = fetcher_module.fetch_portal()

        # Should have both incoming and outgoing players
        directions = [r["direction"] for r in result]
        assert "incoming" in directions
        assert "outgoing" in directions
        mock_scraper.fetch_portal_data.assert_called_once_with(
            mock_config.TEAM_247_NAME,
            mock_config.TEAM_247_YEAR,
        )

    def test_handles_fetch_failure(self, mock_config):
        """Should return empty list on fetch failure."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_portal_data.side_effect = Exception("Fetch error")

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", return_value=mock_scraper),
        ):
            result = fetcher_module.fetch_portal()

        assert result == []
