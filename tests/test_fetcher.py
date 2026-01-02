"""Tests for the fetcher module - data fetching and transformation."""

from unittest.mock import MagicMock, patch

from cfb_cli import Player, Recruit, RecruitData, RecruitStatus, TransferPortalData, TransferStatus

from cfb_tracker import fetcher as fetcher_module
from cfb_tracker.fetcher import (
    _merge_records,
    _portal_to_dict,
    _recruit_to_dict,
)


class TestRecruitToDict:
    """Tests for _recruit_to_dict function."""

    def test_converts_all_fields(self, cfb_recruit):
        """Should convert recruit object to dictionary with all fields."""
        result = _recruit_to_dict(cfb_recruit, "247")

        assert result["name"] == "John Smith"
        assert result["position"] == "qb"  # Normalized from "Quarterback"
        assert result["hometown"] == "Birmingham, AL"
        assert result["stars"] == 4
        assert result["rating"] == 0.95
        assert result["status"] == RecruitStatus.COMMITTED
        assert result["player_url"] == "https://247sports.com/player/john-smith"
        assert result["source"] == "247"
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

        result = _recruit_to_dict(recruit, "on3")

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

        result = _recruit_to_dict(recruit, "247")

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

        result = _recruit_to_dict(recruit, "on3")

        assert result["status"] is None

    def test_handles_none_url(self, cfb_recruit_no_url):
        """Should handle recruits without player URL."""
        result = _recruit_to_dict(cfb_recruit_no_url, "on3")

        assert result["player_url"] is None

    def test_generates_consistent_entry_id(self):
        """Should generate consistent entry_id for same name."""
        recruit1 = Recruit(name="John Smith", position="QB", hometown="City A", stars=4, rating=0.9)
        recruit2 = Recruit(name="John Smith", position="WR", hometown="City B", stars=3, rating=0.8)

        result1 = _recruit_to_dict(recruit1, "247")
        result2 = _recruit_to_dict(recruit2, "on3")

        assert result1["entry_id"] == result2["entry_id"]


class TestPortalToDict:
    """Tests for _portal_to_dict function."""

    def test_converts_incoming_player(self, cfb_portal_player_incoming):
        """Should convert incoming portal player to dictionary."""
        result = _portal_to_dict(cfb_portal_player_incoming, "incoming", "247")

        assert result["name"] == "Alex Williams"
        assert result["position"] == "rb"  # Normalized from "Running Back"
        assert result["direction"] == "incoming"
        assert result["source_school"] == "Alabama"
        assert result["status"] == TransferStatus.COMMITTED
        assert result["player_url"] == "https://247sports.com/player/alex-williams"
        assert result["source"] == "247"

    def test_converts_outgoing_player(self, cfb_portal_player_outgoing):
        """Should convert outgoing portal player to dictionary."""
        result = _portal_to_dict(cfb_portal_player_outgoing, "outgoing", "on3")

        assert result["direction"] == "outgoing"
        assert result["source_school"] is None
        assert result["status"] == TransferStatus.ENTERED
        assert result["player_url"] == "https://on3.com/player/chris-davis"

    def test_handles_none_attributes(self):
        """Should handle players with None optional attributes."""
        player = Player(
            name="Test Player",
            position="QB",
            source_school=None,
            status=None,
            player_url=None,
        )

        result = _portal_to_dict(player, "incoming", "on3")

        assert result["source_school"] is None
        assert result["status"] is None
        assert result["player_url"] is None


class TestMergeRecords:
    """Tests for _merge_records function."""

    def test_merge_unique_records(self):
        """Should keep all unique records."""
        records = [
            {"entry_id": "id1", "name": "Player 1", "source": "247"},
            {"entry_id": "id2", "name": "Player 2", "source": "on3"},
        ]

        result = _merge_records(records)

        assert len(result) == 2

    def test_merge_duplicates_247_authoritative(self):
        """247 data should take priority over on3 for duplicate entries."""
        records = [
            {
                "entry_id": "same-id",
                "name": "Player",
                "stars": 3,
                "status": "uncommitted",
                "player_url": "https://on3.com/player",
                "source": "on3",
            },
            {
                "entry_id": "same-id",
                "name": "Player",
                "stars": 4,
                "status": "committed",
                "player_url": "https://247.com/player",
                "source": "247",
            },
        ]

        result = _merge_records(records)

        assert len(result) == 1
        assert result[0]["stars"] == 4  # 247 value
        assert result[0]["status"] == "committed"  # 247 value
        assert result[0]["player_url"] == "https://247.com/player"  # 247 value
        assert "247" in result[0]["source"]
        assert "on3" in result[0]["source"]

    def test_merge_on3_fills_gaps(self):
        """on3 should fill in missing values from 247."""
        records = [
            {
                "entry_id": "same-id",
                "name": "Player",
                "stars": None,
                "status": None,
                "player_url": None,
                "source": "247",
            },
            {
                "entry_id": "same-id",
                "name": "Player",
                "stars": 4,
                "status": "committed",
                "player_url": "https://on3.com/player",
                "source": "on3",
            },
        ]

        result = _merge_records(records)

        assert len(result) == 1
        assert result[0]["stars"] == 4  # Filled from on3
        assert result[0]["status"] == "committed"  # Filled from on3
        assert result[0]["player_url"] == "https://on3.com/player"  # Filled from on3

    def test_merge_tracks_both_sources(self):
        """Should track both sources when records are merged."""
        records = [
            {"entry_id": "same-id", "name": "Player", "source": "on3"},
            {"entry_id": "same-id", "name": "Player", "source": "247"},
        ]

        result = _merge_records(records)

        assert len(result) == 1
        sources = result[0]["source"].split(",")
        assert "247" in sources
        assert "on3" in sources

    def test_merge_player_url_field(self):
        """Should include player_url in merge fields."""
        records = [
            {
                "entry_id": "same-id",
                "name": "Player",
                "player_url": None,
                "source": "247",
            },
            {
                "entry_id": "same-id",
                "name": "Player",
                "player_url": "https://on3.com/player",
                "source": "on3",
            },
        ]

        result = _merge_records(records)

        assert result[0]["player_url"] == "https://on3.com/player"


class TestFetchRecruits:
    """Tests for fetch_recruits function."""

    def test_fetches_from_both_sources(self, mock_config, cfb_recruit_data):
        """Should fetch and merge recruits from On3 and 247."""
        mock_scraper_on3 = MagicMock()
        mock_scraper_247 = MagicMock()

        mock_scraper_on3.fetch_recruit_data.return_value = cfb_recruit_data
        mock_scraper_247.fetch_recruit_data.return_value = RecruitData(team="Test", year=2026, recruits=[])

        def get_scraper_side_effect(source, headless=True):
            if source == "on3":
                return mock_scraper_on3
            return mock_scraper_247

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", side_effect=get_scraper_side_effect),
        ):
            result = fetcher_module.fetch_recruits()

        assert len(result) >= 1
        mock_scraper_on3.fetch_recruit_data.assert_called_once()
        mock_scraper_247.fetch_recruit_data.assert_called_once()

    def test_handles_on3_failure(self, mock_config, cfb_recruit):
        """Should continue if On3 fetch fails."""
        mock_scraper_on3 = MagicMock()
        mock_scraper_247 = MagicMock()

        mock_scraper_on3.fetch_recruit_data.side_effect = Exception("On3 error")
        mock_scraper_247.fetch_recruit_data.return_value = RecruitData(
            team="Test",
            year=2026,
            recruits=[cfb_recruit],
        )

        def get_scraper_side_effect(source, headless=True):
            if source == "on3":
                return mock_scraper_on3
            return mock_scraper_247

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", side_effect=get_scraper_side_effect),
        ):
            result = fetcher_module.fetch_recruits()

        # Should still return 247 data
        assert len(result) >= 1

    def test_handles_247_failure(self, mock_config, cfb_recruit):
        """Should continue if 247 fetch fails."""
        mock_scraper_on3 = MagicMock()
        mock_scraper_247 = MagicMock()

        mock_scraper_on3.fetch_recruit_data.return_value = RecruitData(
            team="Test",
            year=2026,
            recruits=[cfb_recruit],
        )
        mock_scraper_247.fetch_recruit_data.side_effect = Exception("247 error")

        def get_scraper_side_effect(source, headless=True):
            if source == "on3":
                return mock_scraper_on3
            return mock_scraper_247

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", side_effect=get_scraper_side_effect),
        ):
            result = fetcher_module.fetch_recruits()

        # Should still return On3 data
        assert len(result) >= 1


class TestFetchPortal:
    """Tests for fetch_portal function."""

    def test_fetches_incoming_and_outgoing(self, mock_config, cfb_portal_data):
        """Should fetch and process both incoming and outgoing portal players."""
        mock_scraper_on3 = MagicMock()
        mock_scraper_247 = MagicMock()

        mock_scraper_on3.fetch_portal_data.return_value = cfb_portal_data
        mock_scraper_247.fetch_portal_data.return_value = TransferPortalData(
            team="Test",
            year=2026,
            incoming=[],
            outgoing=[],
        )

        def get_scraper_side_effect(source, headless=True):
            if source == "on3":
                return mock_scraper_on3
            return mock_scraper_247

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", side_effect=get_scraper_side_effect),
        ):
            result = fetcher_module.fetch_portal()

        # Should have both incoming and outgoing players
        directions = [r["direction"] for r in result]
        assert "incoming" in directions
        assert "outgoing" in directions

    def test_handles_portal_fetch_failure(self, mock_config):
        """Should handle portal fetch failures gracefully."""
        mock_scraper = MagicMock()
        mock_scraper.fetch_portal_data.side_effect = Exception("Portal error")

        with (
            patch.object(fetcher_module, "config", mock_config),
            patch.object(fetcher_module, "get_scraper", return_value=mock_scraper),
        ):
            result = fetcher_module.fetch_portal()

        # Should return empty list on failure
        assert result == []
