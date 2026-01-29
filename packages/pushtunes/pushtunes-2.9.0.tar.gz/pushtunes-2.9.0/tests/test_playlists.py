"""Tests for Playlist services (PlaylistComparer, PlaylistPusher)."""

import unittest
from unittest.mock import MagicMock, patch
from pushtunes.models.playlist import Playlist
from pushtunes.models.track import Track
from pushtunes.services.playlist_comparer import PlaylistComparer
from pushtunes.services.playlist_pusher import PlaylistPusher, ConflictMode
from pushtunes.services.music_service import MusicService


class TestPlaylistComparer(unittest.TestCase):
    """Test PlaylistComparer logic."""

    def setUp(self):
        self.track1 = Track(artists=["Pink Floyd"], title="Time")
        self.track2 = Track(artists=["Daft Punk"], title="Digital Love")
        self.track3 = Track(artists=["Lorn"], title="Acid Rain")

    def test_compare_playlists_basic(self):
        """Test basic playlist comparison."""
        source = Playlist(name="Source", tracks=[self.track1, self.track2])
        target = Playlist(name="Target", tracks=[self.track1, self.track3])
        
        comparer = PlaylistComparer(playlist_source=source, playlist_target=target)
        result = comparer.compare_playlists()
        
        self.assertEqual(result.source_track_count, 2)
        self.assertEqual(result.target_track_count, 2)
        self.assertEqual(len(result.tracks_in_both), 1)
        self.assertEqual(len(result.tracks_only_in_source), 1)
        self.assertEqual(len(result.tracks_only_in_target), 1)
        self.assertEqual(result.tracks_in_both[0][0], self.track1)


class TestPlaylistPusher(unittest.TestCase):
    """Test PlaylistPusher logic."""

    def setUp(self):
        self.mock_service = MagicMock(spec=MusicService)
        self.mock_service.service_name = "mock_service"
        self.track1 = Track(artists=["Pink Floyd"], title="Time", service_id="id1")
        self.track2 = Track(artists=["Daft Punk"], title="Digital Love", service_id="id2")
        self.playlist = Playlist(name="Test Playlist", tracks=[self.track1, self.track2])

    def test_push_playlist_new(self):
        """Test pushing a new playlist (no conflict)."""
        # Setup: No existing playlist
        self.mock_service.get_user_playlists.return_value = []
        self.mock_service.search_tracks.side_effect = [[self.track1], [self.track2]]
        self.mock_service.create_playlist.return_value = "new_pl_id"
        self.mock_service.add_tracks_to_playlist.return_value = True
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            # Return (match, score)
            mock_best.side_effect = [(self.track1, 1.0), (self.track2, 1.0)]
            result = pusher.push_playlist()
            
            self.assertTrue(result.success)
            self.assertEqual(result.playlist_id, "new_pl_id")
            self.mock_service.create_playlist.assert_called_with(
                name="Test Playlist", 
                description="Imported playlist with 2 tracks"
            )
            self.mock_service.add_tracks_to_playlist.assert_called_with("new_pl_id", ["id1", "id2"])

    def test_push_playlist_conflict_abort(self):
        """Test conflict mode 'abort'."""
        # Setup: Existing playlist with same name
        self.mock_service.get_user_playlists.return_value = [{"id": "ex_id", "name": "Test Playlist"}]
        self.mock_service.get_playlist_tracks.return_value = [self.track1]
        self.mock_service.search_tracks.side_effect = [[self.track1], [self.track2]]
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service,
            conflict_mode=ConflictMode.abort
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            # 1. _match_track(track1) -> (track1, 1.0)
            # 2. _match_track(track2) -> (track2, 1.0)
            # 3. _analyze_conflict: check track1 in existing -> (track1, 1.0)
            # 4. _analyze_conflict: check track2 in existing -> (None, 0.0)
            # 5. _analyze_conflict: find tracks to remove: check existing track1 in source -> (track1, 1.0)
            mock_best.side_effect = [
                (self.track1, 1.0), (self.track2, 1.0),
                (self.track1, 1.0), (None, 0.0), (self.track1, 1.0)
            ]
            result = pusher.push_playlist()
            
            self.assertFalse(result.success)
            self.assertIsNotNone(result.conflict)
            self.assertEqual(result.playlist_id, "ex_id")

    def test_push_playlist_conflict_replace(self):
        """Test conflict mode 'replace'."""
        self.mock_service.get_user_playlists.return_value = [{"id": "ex_id", "name": "Test Playlist"}]
        self.mock_service.get_playlist_tracks.return_value = [self.track1]
        self.mock_service.search_tracks.side_effect = [[self.track1], [self.track2]]
        self.mock_service.replace_playlist_tracks.return_value = True
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service,
            conflict_mode=ConflictMode.replace
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            # 1. _match_track(track1) -> (track1, 1.0)
            # 2. _match_track(track2) -> (track2, 1.0)
            # 3. _analyze_conflict: check track1 in existing -> (track1, 1.0)
            # 4. _analyze_conflict: check track2 in existing -> (None, 0.0)
            # 5. _analyze_conflict: check existing track1 in source -> (track1, 1.0)
            mock_best.side_effect = [
                (self.track1, 1.0), (self.track2, 1.0),
                (self.track1, 1.0), (None, 0.0), (self.track1, 1.0)
            ]
            result = pusher.push_playlist()
            
            self.assertTrue(result.success)
            self.mock_service.replace_playlist_tracks.assert_called_with("ex_id", ["id1", "id2"])

    def test_push_playlist_conflict_sync(self):
        """Test conflict mode 'sync'."""
        self.mock_service.get_user_playlists.return_value = [{"id": "ex_id", "name": "Test Playlist"}]
        # Existing has track3 which should be removed
        self.mock_service.get_playlist_tracks.return_value = [self.track1, Track(artists=["A"], title="T3", service_id="id3")]
        self.mock_service.search_tracks.side_effect = [[self.track1], [self.track2]]
        self.mock_service.remove_tracks_from_playlist.return_value = True
        self.mock_service.replace_playlist_tracks.return_value = True
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service,
            conflict_mode=ConflictMode.sync
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            # Matches for track1, track2, and conflict detection
            mock_best.side_effect = [
                (self.track1, 1.0), (self.track2, 1.0),
                (self.track1, 1.0), (None, 0.0), (self.track1, 1.0), (None, 0.0)
            ]
            result = pusher.push_playlist()
            
            self.assertTrue(result.success)
            self.mock_service.remove_tracks_from_playlist.assert_called()

    def test_push_playlist_require_all_tracks_fail(self):
        """Test that push fails if require_all_tracks is True and some tracks fail."""
        self.mock_service.get_user_playlists.return_value = []
        self.mock_service.search_tracks.side_effect = [[self.track1], []]
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service,
            require_all_tracks=True
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            mock_best.side_effect = [(self.track1, 1.0), (None, 0.0)]
            result = pusher.push_playlist()
            self.assertFalse(result.success)
            self.assertIn("could not be matched", result.message)

    def test_push_playlist_append_mode(self):
        """Test conflict mode 'append'."""
        self.mock_service.get_user_playlists.return_value = [{"id": "ex_id", "name": "Test Playlist"}]
        # Existing has track1, track2 is missing
        self.mock_service.get_playlist_tracks.return_value = [self.track1]
        self.mock_service.search_tracks.side_effect = [[self.track1], [self.track2]]
        self.mock_service.add_tracks_to_playlist.return_value = True
        
        pusher = PlaylistPusher(
            playlist=self.playlist,
            service=self.mock_service,
            conflict_mode=ConflictMode.append
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            # Matches for track1, track2, and conflict detection
            mock_best.side_effect = [
                (self.track1, 1.0), (self.track2, 1.0),
                (self.track1, 1.0), (None, 0.0), (self.track1, 1.0)
            ]
            result = pusher.push_playlist()
            
            self.assertTrue(result.success)
            self.mock_service.add_tracks_to_playlist.assert_called_with("ex_id", ["id2"])

    def test_push_playlist_target_id(self):
        """Test pushing to a specific playlist ID."""
        self.mock_service.search_tracks.return_value = [self.track1]
        self.mock_service.get_playlist_tracks.return_value = []
        self.mock_service.add_tracks_to_playlist.return_value = True
        
        pusher = PlaylistPusher(
            playlist=Playlist(name="Src", tracks=[self.track1]),
            service=self.mock_service,
            target_playlist_id="target_123",
            conflict_mode=ConflictMode.append
        )
        
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            mock_best.return_value = (self.track1, 1.0)
            result = pusher.push_playlist()
            self.assertEqual(result.playlist_id, "target_123")

    def test_create_playlist_failure(self):
        """Test failure when creating a new playlist."""
        self.mock_service.get_user_playlists.return_value = []
        self.mock_service.search_tracks.return_value = [self.track1]
        self.mock_service.create_playlist.return_value = None # Fails
        
        pusher = PlaylistPusher(playlist=Playlist(name="S", tracks=[self.track1]), service=self.mock_service)
        with patch('pushtunes.services.playlist_pusher.get_best_match') as mock_best:
            mock_best.return_value = (self.track1, 1.0)
            result = pusher.push_playlist()
            self.assertFalse(result.success)
            self.assertEqual(result.message, "Failed to create playlist")
