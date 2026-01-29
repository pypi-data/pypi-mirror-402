"""Tests for DeletionManager utility."""

import unittest
import unittest.mock
import os
import tempfile
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.utils.deletion_manager import DeletionManager
from pushtunes.services.mappings_manager import MappingsManager


class TestDeletionManager(unittest.TestCase):
    """Test DeletionManager logic."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_dir = self.temp_dir.name
        self.manager = DeletionManager(backup_dir=self.backup_dir)
        
        self.album1 = Album(artists=["Pink Floyd"], title="The Wall", service_id="a1")
        self.album2 = Album(artists=["Daft Punk"], title="Discovery", service_id="a2")
        self.track1 = Track(artists=["Queen"], title="Bohemian Rhapsody", service_id="t1")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_backup_albums(self):
        """Test backing up albums to CSV."""
        backup_file = self.manager.backup_albums([self.album1, self.album2], "test_op")
        self.assertTrue(os.path.exists(backup_file))
        self.assertIn("albums_test_op_backup", backup_file)
        
        # Verify content briefly (using CsvManager internally)
        with open(backup_file, "r") as f:
            content = f.read()
            self.assertIn("Pink Floyd", content)
            self.assertIn("The Wall", content)
            self.assertIn("Daft Punk", content)

    def test_backup_tracks(self):
        """Test backing up tracks to CSV."""
        backup_file = self.manager.backup_tracks([self.track1], "test_op")
        self.assertTrue(os.path.exists(backup_file))
        self.assertIn("tracks_test_op_backup", backup_file)

    def test_generate_deletion_preview_basic(self):
        """Test preview without mappings."""
        target_items = [self.album1, self.album2]
        source_items = [self.album1] # album2 is missing from source
        
        preview = self.manager.generate_deletion_preview(
            target_items=target_items,
            source_items=source_items,
            min_similarity=0.8
        )
        
        self.assertEqual(preview.total_target_items, 2)
        self.assertEqual(len(preview.items_to_delete), 1)
        self.assertEqual(preview.items_to_delete[0].item, self.album2)
        self.assertEqual(len(preview.items_preserved), 1)
        self.assertEqual(preview.items_preserved[0].item, self.album1)

    def test_generate_deletion_preview_with_mappings(self):
        """Test preview with mappings ensuring mapped items are preserved."""
        # album2 is in target. album3 is in source. 
        # mapping says album3 -> album2.
        album3 = Album(artists=["Mapped Artist"], title="Mapped Title")
        target_items = [self.album2]
        source_items = [album3]
        
        mock_mappings = unittest.mock.MagicMock(spec=MappingsManager)
        mock_mappings.get_album_mapping.return_value = self.album2
        
        preview = self.manager.generate_deletion_preview(
            target_items=target_items,
            source_items=source_items,
            min_similarity=0.8,
            mappings=mock_mappings,
            service_name="spotify"
        )
        
        self.assertEqual(len(preview.items_to_delete), 0)
        self.assertEqual(len(preview.items_preserved), 1)
        self.assertEqual(preview.items_preserved[0].item, self.album2)
        self.assertTrue(preview.items_preserved[0].will_be_deleted is False)
