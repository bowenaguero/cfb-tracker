"""Tests for the db module - team-scoped database operations."""

from unittest.mock import MagicMock, patch

import pytest

from cfb_tracker import db as db_module


class TestGetTeamId:
    """Tests for get_team_id function."""

    def test_returns_team_from_config(self, mock_config):
        """Should return TEAM from config."""
        with patch.object(db_module, "config", mock_config):
            result = db_module.get_team_id()
        assert result == "Test Tigers"

    def test_raises_when_team_not_set(self):
        """Should raise ValueError when TEAM is not configured."""
        mock_config = MagicMock()
        mock_config.TEAM = None

        with patch.object(db_module, "config", mock_config):
            with pytest.raises(ValueError, match="TEAM environment variable"):
                db_module.get_team_id()

    def test_raises_when_team_is_empty_string(self):
        """Should raise ValueError when TEAM is empty string."""
        mock_config = MagicMock()
        mock_config.TEAM = ""

        with patch.object(db_module, "config", mock_config):
            with pytest.raises(ValueError, match="TEAM environment variable"):
                db_module.get_team_id()


class TestGetAllRecords:
    """Tests for get_all_records with team filtering."""

    def test_filters_by_team_id(self, mock_config):
        """Should filter records by team_id."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.get_all_records("recruits")

        mock_client.table.assert_called_once_with("recruits")
        mock_table.select.assert_called_once_with("*")
        mock_table.eq.assert_called_once_with("team_id", "Test Tigers")

    def test_returns_data_from_response(self, mock_config):
        """Should return data from Supabase response."""
        expected_data = [{"entry_id": "abc", "name": "Test Player"}]

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=expected_data)

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            result = db_module.get_all_records("recruits")

        assert result == expected_data


class TestUpsertRecords:
    """Tests for upsert_records with team_id injection."""

    def test_does_nothing_when_records_empty(self, mock_config):
        """Should return early when records list is empty."""
        mock_client = MagicMock()

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.upsert_records("recruits", [])

        mock_client.table.assert_not_called()

    def test_adds_team_id_to_records(self, mock_config):
        """Should add team_id to each record before upsert."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        records = [{"entry_id": "abc", "name": "Test Player"}]

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.upsert_records("recruits", records)

        call_args = mock_table.upsert.call_args
        upserted_records = call_args[0][0]
        assert len(upserted_records) == 1
        assert upserted_records[0]["team_id"] == "Test Tigers"
        assert upserted_records[0]["entry_id"] == "abc"
        assert upserted_records[0]["name"] == "Test Player"

    def test_uses_composite_on_conflict(self, mock_config):
        """Should use team_id,entry_id for conflict resolution."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.upsert_records("recruits", [{"entry_id": "abc"}])

        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "team_id,entry_id"

    def test_upserts_multiple_records(self, mock_config):
        """Should add team_id to all records."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        records = [
            {"entry_id": "abc", "name": "Player 1"},
            {"entry_id": "def", "name": "Player 2"},
        ]

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.upsert_records("recruits", records)

        call_args = mock_table.upsert.call_args
        upserted_records = call_args[0][0]
        assert len(upserted_records) == 2
        assert all(r["team_id"] == "Test Tigers" for r in upserted_records)


class TestDeleteRecords:
    """Tests for delete_records with team scoping."""

    def test_does_nothing_when_ids_empty(self, mock_config):
        """Should return early when ids list is empty."""
        mock_client = MagicMock()

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.delete_records("recruits", [])

        mock_client.table.assert_not_called()

    def test_scopes_delete_to_team(self, mock_config):
        """Should filter delete by team_id."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.delete_records("recruits", ["id1", "id2"])

        mock_table.eq.assert_called_once_with("team_id", "Test Tigers")
        mock_table.in_.assert_called_once_with("entry_id", ["id1", "id2"])

    def test_deletes_single_record(self, mock_config):
        """Should work with single ID."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        with (
            patch.object(db_module, "get_client", return_value=mock_client),
            patch.object(db_module, "config", mock_config),
        ):
            db_module.delete_records("recruits", ["single-id"])

        mock_table.in_.assert_called_once_with("entry_id", ["single-id"])
