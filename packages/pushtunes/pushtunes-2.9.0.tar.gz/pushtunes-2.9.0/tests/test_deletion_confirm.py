"""Tests for deletion_confirm utility."""

import unittest
from unittest.mock import patch
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.utils.deletion_manager import DeletionPreview, DeletionCandidate
from pushtunes.utils.deletion_confirm import display_deletion_preview, confirm_deletion, display_item_details


class TestDeletionConfirm(unittest.TestCase):
    """Test deletion confirmation logic and display."""

    def setUp(self):
        self.album = Album(artists=["A"], title="T")
        self.candidate = DeletionCandidate(item=self.album, source_match=None, similarity_score=0.0, will_be_deleted=True)
        self.preview = DeletionPreview(total_target_items=1, items_to_delete=[self.candidate], items_preserved=[])

    def test_display_deletion_preview(self):
        """Test display_deletion_preview runs without error."""
        with patch('rich.console.Console.print'):
            display_deletion_preview(self.preview, "albums", 0.8)

    def test_confirm_deletion_yes(self):
        """Test confirm_deletion returns True on 'yes' input."""
        with patch('rich.console.Console.print'):
            with patch('builtins.input', return_value="yes"):
                res = confirm_deletion(self.preview, "albums", "backup.csv")
                self.assertTrue(res)

    def test_confirm_deletion_no(self):
        """Test confirm_deletion returns False on non-'yes' input."""
        with patch('rich.console.Console.print'):
            with patch('builtins.input', return_value="no"):
                res = confirm_deletion(self.preview, "albums", "backup.csv")
                self.assertFalse(res)

    def test_display_item_details(self):
        """Test item detail formatting."""
        album = Album(artists=["Artist"], title="Album")
        self.assertEqual(display_item_details(album, "album"), "Artist - Album")
        
        track = Track(artists=["Artist"], title="Track", album="Album")
        self.assertEqual(display_item_details(track, "track"), "Artist - Track (from Album)")
        
        track_no_album = Track(artists=["Artist"], title="Track")
        self.assertEqual(display_item_details(track_no_album, "track"), "Artist - Track")
