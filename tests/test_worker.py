"""Tests for the worker module - social media message generation."""

from cfb_tracker.worker import (
    EMOJI_COMMITTED,
    EMOJI_DECOMMITTED,
    EMOJI_PORTAL_ENTER,
    EMOJI_PORTAL_WITHDRAW,
    EMOJI_SIGNED,
    _build_message,
    _format_stars,
    _format_url_line,
)


class TestFormatStars:
    """Tests for _format_stars helper."""

    def test_four_stars(self):
        result = _format_stars(4)
        assert result == "\u2b50\u2b50\u2b50\u2b50"
        assert result.count("\u2b50") == 4

    def test_five_stars(self):
        assert _format_stars(5).count("\u2b50") == 5

    def test_three_stars(self):
        assert _format_stars(3).count("\u2b50") == 3

    def test_one_star(self):
        assert _format_stars(1).count("\u2b50") == 1

    def test_zero_stars(self):
        assert _format_stars(0) == ""

    def test_none_stars(self):
        assert _format_stars(None) == ""

    def test_negative_stars(self):
        assert _format_stars(-1) == ""


class TestFormatUrlLine:
    """Tests for _format_url_line helper."""

    def test_with_url(self):
        url = "https://247sports.com/player/john-smith"
        result = _format_url_line(url)
        assert result == f"\n\n{url}"

    def test_without_url(self):
        assert _format_url_line(None) == ""
        assert _format_url_line("") == ""


class TestBuildMessageRecruitsCommitted:
    """Tests for recruit commitment messages."""

    def test_committed_with_url(self):
        player = {
            "name": "John Smith",
            "position": "QB",
            "stars": 4,
            "player_url": "https://247sports.com/player/john-smith",
        }
        data = {"status": "committed"}

        result = _build_message("new_player", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_COMMITTED)
        assert "John Smith" in result
        assert "\u2b50\u2b50\u2b50\u2b50" in result  # 4 stars
        assert "QB" in result
        assert "has committed to the Auburn Tigers" in result
        assert "https://247sports.com/player/john-smith" in result

    def test_committed_without_url(self):
        player = {
            "name": "John Smith",
            "position": "QB",
            "stars": 4,
            "player_url": None,
        }
        data = {"status": "committed"}

        result = _build_message("new_player", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_COMMITTED)
        assert "has committed to the Auburn Tigers" in result
        assert result.count("\n\n") == 0  # No URL line

    def test_committed_status_change(self):
        player = {
            "name": "John Smith",
            "position": "QB",
            "stars": 5,
            "player_url": "https://example.com",
        }
        data = {"new_status": "committed", "old_status": "uncommitted"}

        result = _build_message("status_change", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_COMMITTED)
        assert "has committed to the Auburn Tigers" in result


class TestBuildMessageRecruitsDecommitted:
    """Tests for recruit decommitment messages."""

    def test_decommitted_with_url(self):
        player = {
            "name": "Mike Johnson",
            "position": "WR",
            "stars": 3,
            "player_url": "https://247sports.com/player/mike-johnson",
        }
        data = {"new_status": "decommitted", "old_status": "committed"}

        result = _build_message("status_change", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_DECOMMITTED)
        assert "Mike Johnson" in result
        assert "\u2b50\u2b50\u2b50" in result  # 3 stars
        assert "WR" in result
        assert "has decommitted from the Auburn Tigers" in result
        assert "https://247sports.com/player/mike-johnson" in result

    def test_decommitted_without_url(self):
        player = {
            "name": "Mike Johnson",
            "position": "WR",
            "stars": 3,
            "player_url": None,
        }
        data = {"new_status": "decommitted"}

        result = _build_message("status_change", "recruits", "Auburn Tigers", player, data)

        assert "has decommitted from the Auburn Tigers" in result
        assert result.count("\n\n") == 0


class TestBuildMessageRecruitsSigned:
    """Tests for recruit signing messages."""

    def test_signed_status(self):
        player = {
            "name": "John Smith",
            "position": "QB",
            "stars": 4,
            "player_url": "https://example.com",  # Should NOT appear in signed messages
        }
        data = {"new_status": "signed"}

        result = _build_message("status_change", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_SIGNED)
        assert "has signed with the Auburn Tigers" in result
        # Signed messages should NOT include URL
        assert "https://example.com" not in result

    def test_enrolled_status(self):
        player = {
            "name": "John Smith",
            "position": "QB",
            "stars": 4,
            "player_url": "https://example.com",
        }
        data = {"new_status": "enrolled"}

        result = _build_message("status_change", "recruits", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_SIGNED)
        assert "has signed with the Auburn Tigers" in result


class TestBuildMessagePortalOutgoing:
    """Tests for outgoing portal messages (players leaving team)."""

    def test_entered_portal_with_url(self):
        player = {
            "name": "Chris Davis",
            "position": "LB",
            "direction": "outgoing",
            "source_school": None,
            "player_url": "https://on3.com/player/chris-davis",
        }
        data = {"status": None}

        result = _build_message("new_player", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_PORTAL_ENTER)
        assert "Auburn Tigers LB Chris Davis has entered the transfer portal" in result
        assert "https://on3.com/player/chris-davis" in result

    def test_entered_portal_without_url(self):
        player = {
            "name": "Chris Davis",
            "position": "LB",
            "direction": "outgoing",
            "player_url": None,
        }
        data = {}

        result = _build_message("new_player", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_PORTAL_ENTER)
        assert "has entered the transfer portal" in result
        assert result.count("\n\n") == 0

    def test_withdrawn_from_portal(self):
        player = {
            "name": "Chris Davis",
            "position": "LB",
            "direction": "outgoing",
            "player_url": "https://example.com",
        }
        data = {}

        result = _build_message("player_removed", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_PORTAL_WITHDRAW)
        assert "Auburn Tigers LB Chris Davis has withdrawn from the transfer portal" in result
        assert "https://example.com" in result


class TestBuildMessagePortalIncoming:
    """Tests for incoming portal messages (players transferring to team)."""

    def test_committed_with_source_school(self):
        player = {
            "name": "Alex Williams",
            "position": "RB",
            "direction": "incoming",
            "source_school": "Alabama",
            "player_url": "https://247sports.com/player/alex-williams",
        }
        data = {"status": "committed"}

        result = _build_message("new_player", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_COMMITTED)
        assert "Alabama RB Alex Williams has committed to the Auburn Tigers" in result
        assert "https://247sports.com/player/alex-williams" in result

    def test_committed_without_source_school(self):
        player = {
            "name": "Alex Williams",
            "position": "RB",
            "direction": "incoming",
            "source_school": "",
            "player_url": "https://example.com",
        }
        data = {"status": "committed"}

        result = _build_message("new_player", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_COMMITTED)
        # Should still work even without source school
        assert "Alex Williams" in result
        assert "has committed to the Auburn Tigers" in result

    def test_signed_portal_transfer(self):
        player = {
            "name": "Alex Williams",
            "position": "RB",
            "direction": "incoming",
            "source_school": "Alabama",
            "player_url": "https://example.com",  # Should NOT appear
        }
        data = {"new_status": "signed"}

        result = _build_message("status_change", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_SIGNED)
        assert "Alabama RB Alex Williams has signed with the Auburn Tigers" in result
        # Signed messages should NOT include URL
        assert "https://example.com" not in result

    def test_enrolled_portal_transfer(self):
        player = {
            "name": "Alex Williams",
            "position": "RB",
            "direction": "incoming",
            "source_school": "Alabama",
            "player_url": "https://example.com",
        }
        data = {"new_status": "enrolled"}

        result = _build_message("status_change", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_SIGNED)
        assert "has signed with the Auburn Tigers" in result

    def test_decommitted_portal_transfer(self):
        player = {
            "name": "Alex Williams",
            "position": "RB",
            "direction": "incoming",
            "source_school": "Alabama",
            "player_url": "https://example.com",
        }
        data = {}

        result = _build_message("player_removed", "portal", "Auburn Tigers", player, data)

        assert result.startswith(EMOJI_DECOMMITTED)
        assert "Alabama RB Alex Williams has decommitted from the Auburn Tigers" in result
        assert "https://example.com" in result


class TestBuildMessageFallback:
    """Tests for fallback message handling."""

    def test_unknown_event_type(self):
        player = {"name": "Test Player", "position": "QB"}
        data = {}

        result = _build_message("unknown_event", "recruits", "Auburn Tigers", player, data)

        assert "Player update: Test Player (QB) - Auburn Tigers" in result

    def test_unknown_status(self):
        player = {
            "name": "Test Player",
            "position": "QB",
            "stars": 3,
            "player_url": None,
        }
        data = {"status": "unknown_status"}

        result = _build_message("new_player", "recruits", "Auburn Tigers", player, data)

        # Should fall through to fallback
        assert "Player update:" in result


class TestEmojiConstants:
    """Tests that emoji constants are properly defined."""

    def test_committed_emoji(self):
        assert EMOJI_COMMITTED == "\u2705"  # ✅

    def test_decommitted_emoji(self):
        assert EMOJI_DECOMMITTED == "\U0001f614"  # 😔

    def test_signed_emoji(self):
        assert EMOJI_SIGNED == "\U0001f4dd"  # 📝

    def test_portal_enter_emoji(self):
        assert EMOJI_PORTAL_ENTER == "\U0001f6a8"  # 🚨

    def test_portal_withdraw_emoji(self):
        assert EMOJI_PORTAL_WITHDRAW == "\u21a9\ufe0f"  # ↩️
