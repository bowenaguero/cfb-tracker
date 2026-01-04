"""Tests for the sync module - database synchronization and event queueing."""

from unittest.mock import MagicMock, patch

from cfb_tracker import sync as sync_module


class TestSyncTable:
    """Tests for sync_table function."""

    def test_sync_new_records(self, sample_recruit):
        """Should upsert new records and enqueue new_player events."""
        mock_db = MagicMock()
        mock_db.get_all_records.return_value = []  # No existing records
        mock_enqueue = MagicMock()

        fresh_records = [sample_recruit]

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", fresh_records)

        assert result["upserted"] == 1
        assert result["deleted"] == 0

        mock_db.upsert_records.assert_called_once()
        mock_enqueue.assert_called_once_with(
            event_type="new_player",
            table="recruits",
            player_data=sample_recruit,
        )

    def test_sync_status_change(self, sample_recruit):
        """Should enqueue status_change event when status changes."""
        existing_record = {**sample_recruit, "status": "uncommitted"}
        new_record = {**sample_recruit, "status": "committed"}

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = [existing_record]
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", [new_record])

        assert result["upserted"] == 1
        mock_enqueue.assert_called_once_with(
            event_type="status_change",
            table="recruits",
            player_data=new_record,
            old_status="uncommitted",
            new_status="committed",
        )

    def test_sync_no_changes(self, sample_recruit):
        """Should not upsert or enqueue when record is unchanged."""
        mock_db = MagicMock()
        mock_db.get_all_records.return_value = [sample_recruit]
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", [sample_recruit])

        assert result["upserted"] == 0
        assert result["deleted"] == 0
        mock_db.upsert_records.assert_not_called()
        mock_enqueue.assert_not_called()

    def test_sync_deletes_stale_records(self, sample_recruit):
        """Should delete records no longer in source and enqueue player_removed."""
        existing_record = {**sample_recruit, "entry_id": "old-id"}

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = [existing_record]
        mock_enqueue = MagicMock()

        # Fresh records don't include the old record
        fresh_records = []

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", fresh_records)

        assert result["deleted"] == 1
        mock_db.delete_records.assert_called_once_with("recruits", ["old-id"])
        mock_enqueue.assert_called_once_with(
            event_type="player_removed",
            table="recruits",
            player_data=existing_record,
        )

    def test_sync_portal_deletion_enqueues_event(self, sample_portal_outgoing):
        """Should enqueue player_removed for portal deletions."""
        mock_db = MagicMock()
        mock_db.get_all_records.return_value = [sample_portal_outgoing]
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("portal", [])  # noqa: F841

        mock_enqueue.assert_called_once_with(
            event_type="player_removed",
            table="portal",
            player_data=sample_portal_outgoing,
        )

    def test_sync_multiple_deletions(self, sample_recruit):
        """Should enqueue player_removed for each deleted record."""
        record1 = {**sample_recruit, "entry_id": "id1", "name": "Player 1"}
        record2 = {**sample_recruit, "entry_id": "id2", "name": "Player 2"}

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = [record1, record2]
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            sync_module.sync_table("recruits", [])

        assert mock_enqueue.call_count == 2
        # Verify both player_removed events were enqueued
        calls = mock_enqueue.call_args_list
        event_types = [c[1]["event_type"] for c in calls]
        assert all(et == "player_removed" for et in event_types)

    def test_sync_adds_updated_at_timestamp(self, sample_recruit):
        """Should add updated_at timestamp to new records."""
        record_without_timestamp = {k: v for k, v in sample_recruit.items() if k != "updated_at"}

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = []
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            sync_module.sync_table("recruits", [record_without_timestamp])

        # Verify upsert was called with updated_at
        upsert_call = mock_db.upsert_records.call_args
        upserted_records = upsert_call[0][1]
        assert len(upserted_records) == 1
        assert "updated_at" in upserted_records[0]


class TestEnqueueHelpers:
    """Tests for private enqueue helper functions."""

    def test_enqueue_new_player_handles_exception(self, sample_recruit):
        """Should log exception but not raise when enqueue fails."""
        mock_enqueue = MagicMock(side_effect=Exception("Queue error"))

        with patch.object(sync_module, "enqueue_event", mock_enqueue):
            # Should not raise
            sync_module._enqueue_new_player_event("recruits", sample_recruit)

    def test_enqueue_status_change_handles_exception(self, sample_recruit):
        """Should log exception but not raise when enqueue fails."""
        mock_enqueue = MagicMock(side_effect=Exception("Queue error"))

        with patch.object(sync_module, "enqueue_event", mock_enqueue):
            # Should not raise
            sync_module._enqueue_status_change_event(
                "recruits",
                sample_recruit,
                old_status="uncommitted",
                new_status="committed",
            )

    def test_enqueue_player_removed_handles_exception(self, sample_recruit):
        """Should log exception but not raise when enqueue fails."""
        mock_enqueue = MagicMock(side_effect=Exception("Queue error"))

        with patch.object(sync_module, "enqueue_event", mock_enqueue):
            # Should not raise
            sync_module._enqueue_player_removed_event("recruits", sample_recruit)


class TestSyncTableIntegration:
    """Integration-style tests for sync_table."""

    def test_full_sync_cycle(self):
        """Test a complete sync cycle with new, changed, and deleted records."""
        existing_records = [
            {"entry_id": "keep", "name": "Keeper", "status": "uncommitted"},
            {"entry_id": "change", "name": "Changer", "status": "uncommitted"},
            {"entry_id": "delete", "name": "Deleter", "status": "committed"},
        ]

        fresh_records = [
            {"entry_id": "keep", "name": "Keeper", "status": "uncommitted"},  # No change
            {"entry_id": "change", "name": "Changer", "status": "committed"},  # Status changed
            {"entry_id": "new", "name": "Newbie", "status": "uncommitted"},  # New record
            # "delete" is not in fresh records - will be deleted
        ]

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = existing_records
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", fresh_records)

        # Should upsert 2 records (changed + new)
        assert result["upserted"] == 2

        # Should delete 1 record
        assert result["deleted"] == 1
        mock_db.delete_records.assert_called_once_with("recruits", ["delete"])

        # Should have 3 events: new_player, status_change, player_removed
        assert mock_enqueue.call_count == 3

        event_types = [c[1]["event_type"] for c in mock_enqueue.call_args_list]
        assert "new_player" in event_types
        assert "status_change" in event_types
        assert "player_removed" in event_types

    def test_deduplicates_fresh_records_by_entry_id(self):
        """Should deduplicate records with same entry_id, keeping last occurrence."""
        # Two records with same entry_id (simulates name collision)
        fresh_records = [
            {"entry_id": "same-id", "name": "John Smith", "status": "uncommitted"},
            {"entry_id": "same-id", "name": "John Smith Jr", "status": "committed"},
        ]

        mock_db = MagicMock()
        mock_db.get_all_records.return_value = []
        mock_enqueue = MagicMock()

        with (
            patch.object(sync_module, "db", mock_db),
            patch.object(sync_module, "enqueue_event", mock_enqueue),
        ):
            result = sync_module.sync_table("recruits", fresh_records)

        # Should only upsert 1 record (deduplicated)
        assert result["upserted"] == 1

        # Verify the last occurrence was kept
        upsert_call = mock_db.upsert_records.call_args
        upserted_records = upsert_call[0][1]
        assert len(upserted_records) == 1
        assert upserted_records[0]["name"] == "John Smith Jr"
        assert upserted_records[0]["status"] == "committed"
