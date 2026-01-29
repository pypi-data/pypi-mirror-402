"""Advanced tests for CsvManager utility."""

import unittest
import os
import csv
import tempfile
from pushtunes.models.album import Album
from pushtunes.models.push_status import PushStatus
from pushtunes.services.pusher import PushResult
from pushtunes.utils.csv_manager import CsvManager, CsvColumns


class TestCsvManagerAdvanced(unittest.TestCase):
    """Test CsvManager advanced logic."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        self.csv_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.unlink(self.csv_path)

    def test_import_albums_multiple_artists(self):
        """Test importing albums with artist2...artist10 columns."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["artist", "artist2", "album", "year"])
            writer.writerow(["A1", "A2", "Album X", "2020"])
            
        albums = CsvManager.import_albums(self.csv_path)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].artists, ["A1", "A2"])

    def test_import_unified_filtering(self):
        """Test filtering by 'type' column during import."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["type", "artist", "album", "track", "year"])
            writer.writerow(["album", "Art", "Alb", "", "2020"])
            writer.writerow(["track", "Art", "", "Trk", "2021"])
            
        albums = CsvManager.import_albums(self.csv_path)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].title, "Alb")
        
        tracks = CsvManager.import_tracks(self.csv_path)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Trk")

    def test_export_results_incremental_mappings(self):
        """Test that mappings export preserves existing user data."""
        # 1. Create initial mappings file
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CsvColumns.MAPPINGS)
            writer.writeheader()
            writer.writerow({
                "type": "album", "artist": "Pink Floyd", "title": "The Wall",
                "spotify_id": "user_id_123" # User-filled
            })
            
        # 2. Export same item + a new item
        album1 = Album(artists=["Pink Floyd"], title="The Wall")
        album2 = Album(artists=["Daft Punk"], title="Discovery")
        results = [
            PushResult(item=album1, status=PushStatus.not_found),
            PushResult(item=album2, status=PushStatus.not_found)
        ]
        
        new_count, unmapped = CsvManager.export_album_results_to_mappings(
            results, ["not_found"], self.csv_path
        )
        
        self.assertEqual(new_count, 1) # Only Daft Punk is new
        self.assertEqual(unmapped, 0) # Pink Floyd was already MAPPED (has ID)
        
        # Verify user data preserved
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            pink_floyd = next(r for r in rows if r["artist"] == "Pink Floyd")
            self.assertEqual(pink_floyd["spotify_id"], "user_id_123")
            self.assertIn("Daft Punk", [r["artist"] for r in rows])

    def test_import_tracks_edge_cases(self):
        """Test track import with title column and invalid years."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["artist", "title", "year"]) # uses 'title' instead of 'track'
            writer.writerow(["A", "T", "not-a-year"])
            
        tracks = CsvManager.import_tracks(self.csv_path)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "T")
        self.assertIsNone(tracks[0].year)

    def test_import_playlist(self):
        """Test importing a playlist from CSV."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["artist", "track", "album"])
            writer.writerow(["A", "T", "Alb"])
            
        playlist = CsvManager.import_playlist(self.csv_path, "Custom Name")
        self.assertEqual(playlist.name, "Custom Name")
        self.assertEqual(len(playlist.tracks), 1)
        self.assertEqual(playlist.tracks[0].title, "T")

    def test_read_existing_mappings_robustness(self):
        """Test reading mappings with missing columns or non-existent file."""
        # 1. Non-existent file
        existing, rows, mapped = CsvManager._read_existing_mappings("nonexistent.csv")
        self.assertEqual(len(existing), 0)
        
        # 2. File with missing columns
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["only_one_col"])
            writer.writerow(["data"])
            
        existing, rows, mapped = CsvManager._read_existing_mappings(self.csv_path)
        self.assertEqual(len(existing), 0)
