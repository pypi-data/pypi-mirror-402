"""Tests for CSV music service."""

import unittest
import os
import tempfile
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.models.playlist import Playlist
from pushtunes.services.csv import CSVService


class TestCSVService(unittest.TestCase):
    """Test CSVService logic."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        self.csv_path = self.temp_file.name
        self.temp_file.close()
        self.service = CSVService(self.csv_path)

    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.unlink(self.csv_path)

    def test_collect_and_write_albums(self):
        """Test collecting albums and writing them to CSV."""
        album = Album(artists=["Pink Floyd"], title="The Wall", year=1979)
        self.service.add_album(album)
        self.assertEqual(len(self.service.collected_albums), 1)
        
        self.service.write_albums_to_csv()
        self.assertTrue(os.path.exists(self.csv_path))
        with open(self.csv_path, "r") as f:
            content = f.read()
            self.assertIn("Pink Floyd", content)
            self.assertIn("The Wall", content)

    def test_collect_and_write_tracks(self):
        """Test collecting tracks and writing them to CSV."""
        track = Track(artists=["Queen"], title="Bohemian Rhapsody")
        self.service.add_track(track)
        self.assertEqual(len(self.service.collected_tracks), 1)
        
        self.service.write_tracks_to_csv()
        self.assertTrue(os.path.exists(self.csv_path))
        with open(self.csv_path, "r") as f:
            content = f.read()
            self.assertIn("Queen", content)
            self.assertIn("Bohemian Rhapsody", content)

    def test_write_playlist(self):
        """Test writing a playlist to CSV."""
        tracks = [Track(artists=["A"], title="T1"), Track(artists=["B"], title="T2")]
        playlist = Playlist(name="My List", tracks=tracks)
        
        self.service.write_playlist_to_csv(playlist)
        self.assertTrue(os.path.exists(self.csv_path))
        with open(self.csv_path, "r") as f:
            content = f.read()
            # Playlist name isn't in CSV file, only tracks are
            self.assertIn("T1", content)
            self.assertIn("T2", content)

    def test_search_and_library_methods(self):
        """Test search and library methods."""
        album = Album(artists=["A"], title="T")
        track = Track(artists=["A"], title="T")
        
        self.assertEqual(self.service.search_albums(album), [album])
        self.assertEqual(self.service.search_tracks(track), [track])
        self.assertFalse(self.service.is_album_in_library(album))
        self.assertFalse(self.service.is_track_in_library(track))
        
        self.service.add_album(album)
        self.service.add_track(track)
        self.assertEqual(self.service.get_library_albums(), [album])
        self.assertEqual(self.service.get_library_tracks(), [track])

    def test_playlist_methods(self):
        """Test remaining playlist methods."""
        self.assertEqual(self.service.create_playlist("MyList"), "MyList")
        self.assertTrue(self.service.add_tracks_to_playlist("id", []))
        self.assertTrue(self.service.replace_playlist_tracks("id", []))
        self.assertTrue(self.service.remove_tracks_from_playlist("id", []))
        self.assertEqual(self.service.get_playlist_tracks("id"), [])

    def test_write_empty_collections(self):
        """Test writing empty collections doesn't crash but logs warning."""
        # Just verify it doesn't crash
        self.service.collected_albums = []
        self.service.write_albums_to_csv()
        
        self.service.collected_tracks = []
        self.service.write_tracks_to_csv()
        
        # Pass a Playlist object instead of None to satisfy type checker
        self.service.write_playlist_to_csv(Playlist(name="Empty", tracks=[]))
