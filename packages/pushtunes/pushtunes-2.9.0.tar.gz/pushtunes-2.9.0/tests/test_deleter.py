"""Tests for Deleter service."""

import unittest
from unittest.mock import MagicMock, patch
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.models.push_status import PushStatus
from pushtunes.services.deleter import Deleter, DeleteResult
from pushtunes.services.music_service import MusicService


class TestDeleter(unittest.TestCase):
    """Test Deleter service logic."""

    def setUp(self):
        self.mock_service = MagicMock(spec=MusicService)
        self.album1 = Album(artists=["Pink Floyd"], title="The Wall", service_id="a1")
        self.album2 = Album(artists=["Daft Punk"], title="Discovery", service_id="a2")

    def test_delete_albums_with_confirmation(self):
        """Test successful album deletion with confirmation."""
        self.mock_service.remove_album.return_value = True
        
        deleter = Deleter(
            items_to_delete=[self.album1, self.album2],
            service=self.mock_service,
            item_type="album",
            require_confirmation=True
        )
        
        # Mock external UI components
        with patch('pushtunes.utils.deletion_confirm.confirm_deletion') as mock_confirm:
            with patch('pushtunes.utils.deletion_confirm.display_deletion_preview'):
                with patch('pushtunes.utils.deletion_manager.DeletionManager.backup_albums') as mock_backup:
                    mock_confirm.return_value = True
                    mock_backup.return_value = "fake_backup.csv"
                    
                    results = deleter.delete()
                    
                    self.assertEqual(len(results), 2)
                    self.assertTrue(all(r.status == PushStatus.deleted for r in results))
                    self.assertEqual(self.mock_service.remove_album.call_count, 2)

    def test_delete_tracks_failure(self):
        """Test behavior when service fails to delete a track."""
        track = Track(artists=["Queen"], title="Bohemian Rhapsody", service_id="t1")
        self.mock_service.remove_track.return_value = False # Failure
        
        deleter = Deleter(
            items_to_delete=[track],
            service=self.mock_service,
            item_type="track",
            require_confirmation=False
        )
        
        with patch('pushtunes.utils.deletion_manager.DeletionManager.backup_tracks') as mock_backup:
            mock_backup.return_value = "fake_backup.csv"
            results = deleter.delete()
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, PushStatus.error)
            self.assertEqual(results[0].message, "Failed to delete")

    def test_delete_cancel_confirmation(self):
        """Test that nothing happens if user cancels confirmation."""
        deleter = Deleter(
            items_to_delete=[self.album1],
            service=self.mock_service,
            item_type="album",
            require_confirmation=True
        )
        
        with patch('pushtunes.utils.deletion_confirm.confirm_deletion') as mock_confirm:
            with patch('pushtunes.utils.deletion_confirm.display_deletion_preview'):
                with patch('pushtunes.utils.deletion_manager.DeletionManager.backup_albums'):
                    mock_confirm.return_value = False # User said NO
                    
                    results = deleter.delete()
                    
                    self.assertEqual(len(results), 0)
                    self.mock_service.remove_album.assert_not_called()

    def test_delete_empty_items(self):
        """Test behavior with empty items list."""
        deleter = Deleter(
            items_to_delete=[],
            service=self.mock_service,
            item_type="album"
        )
        results = deleter.delete()
        self.assertEqual(len(results), 0)

    def test_print_delete_stats(self):
        """Test print_delete_stats helper."""
        from pushtunes.services.deleter import print_delete_stats
        results = [
            DeleteResult(item=self.album1, status=PushStatus.deleted),
            DeleteResult(item=self.album2, status=PushStatus.error, message="fail")
        ]
        # Just verify it runs without error
        with patch('rich.console.Console.print'):
            print_delete_stats(results, "albums", use_color=False)
