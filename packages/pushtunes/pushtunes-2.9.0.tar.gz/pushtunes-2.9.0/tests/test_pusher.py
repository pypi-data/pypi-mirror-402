"""Tests for Pusher services (AlbumPusher, TrackPusher)."""

import unittest
from unittest.mock import MagicMock, patch
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.models.push_status import PushStatus
from pushtunes.services.pusher import (
    AlbumPusher, 
    TrackPusher, 
    PushResult,
    ServiceIdMatchStrategy,
    MappingMatchStrategy,
    SearchMatchStrategy,
    MatchContext
)
from pushtunes.services.music_service import MusicService


class TestPusherLogic(unittest.TestCase):
    """Test the core pusher logic and strategies."""

    def setUp(self):
        self.mock_service = MagicMock(spec=MusicService)
        self.mock_service.service_name = "mock_service"
        self.album = Album(artists=["Artist"], title="Album", year=2020)
        self.track = Track(artists=["Artist"], title="Track", album="Album")

    def test_service_id_match_strategy(self):
        """Test matching using service ID in extra_data."""
        strategy = ServiceIdMatchStrategy()
        operations = MagicMock()
        context = MatchContext(
            item=self.album,
            operations=operations,
            service=self.mock_service,
            mappings=None,
            min_similarity=0.8,
            log=MagicMock()
        )
        
        # 1. No extra_data
        self.album.extra_data = None
        self.assertIsNone(strategy._try_match(context))
        
        # 2. Has extra_data but no ID for this service
        self.album.extra_data = {"other_service_id": "123"}
        operations.get_service_id_key.return_value = "mock_service_id"
        self.assertIsNone(strategy._try_match(context))
        
        # 3. Has ID for this service
        self.album.extra_data = {"mock_service_id": "456"}
        expected_match = Album(artists=["Artist"], title="Album", service_id="456", service_name="mock_service")
        operations.create_item_with_service_id.return_value = expected_match
        
        match = strategy._try_match(context)
        self.assertEqual(match, expected_match)
        operations.create_item_with_service_id.assert_called_with(self.album, "456")

    def test_mapping_match_strategy(self):
        """Test matching using manual mappings."""
        strategy = MappingMatchStrategy()
        mappings = MagicMock()
        mock_ops = MagicMock()
        context = MatchContext(
            item=self.album,
            operations=mock_ops,
            service=self.mock_service,
            mappings=mappings,
            min_similarity=0.8,
            log=MagicMock()
        )
        
        # 1. No mapping found
        mappings.get_album_mapping.return_value = None
        self.assertIsNone(strategy._try_match(context))
        
        # 2. Mapping found with ID
        mapped_album = Album(artists=["Artist X"], title="Album X", service_id="id123")
        mappings.get_album_mapping.return_value = mapped_album
        
        match = strategy._try_match(context)
        self.assertEqual(match, mapped_album)
        
        # 3. Mapping found with metadata only (triggers search)
        mapped_meta = Album(artists=["Artist Y"], title="Album Y")
        mappings.get_album_mapping.return_value = mapped_meta
        mock_ops.search.return_value = [mapped_album] # Found via search
        
        with patch('pushtunes.services.pusher.get_best_match') as mock_best:
            mock_best.return_value = (mapped_album, 1.0)
            match = strategy._try_match(context)
            self.assertEqual(match, mapped_album)

    def test_album_pusher_full_flow(self):
        """Test AlbumPusher orchestration."""
        # Setup mocks
        self.mock_service.is_album_in_library.return_value = False
        self.mock_service.search_albums.return_value = [self.album]
        self.mock_service.add_album.return_value = True
        
        pusher = AlbumPusher(
            items=[self.album],
            service=self.mock_service,
            min_similarity=0.8
        )
        
        with patch('pushtunes.services.pusher.get_best_match') as mock_best:
            mock_best.return_value = (self.album, 1.0)
            results = pusher.push()
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, PushStatus.added)
            self.mock_service.add_album.assert_called()

    def test_track_pusher_already_in_library(self):
        """Test that pusher skips items already in library."""
        self.mock_service.is_track_in_library.return_value = True
        
        pusher = TrackPusher(
            items=[self.track],
            service=self.mock_service
        )
        results = pusher.push()
        
        self.assertEqual(results[0].status, PushStatus.already_in_library)
        self.mock_service.add_track.assert_not_called()

    def test_pusher_not_found(self):
        """Test pusher behavior when no match is found."""
        self.mock_service.is_album_in_library.return_value = False
        self.mock_service.search_albums.return_value = [] # No search results
        
        pusher = AlbumPusher(
            items=[self.album],
            service=self.mock_service
        )
        results = pusher.push()
        self.assertEqual(results[0].status, PushStatus.not_found)

    def test_cross_type_mapping_album_to_track(self):
        """Test mapping an album to a track."""
        mappings = MagicMock()
        # Mapping returns a Track instead of Album
        mapped_track = Track(artists=["A"], title="T", service_id="t1")
        mappings.get_album_mapping.return_value = mapped_track
        self.mock_service.is_album_in_library.return_value = False
        self.mock_service.is_track_in_library.return_value = False
        self.mock_service.add_track.return_value = True
        
        pusher = AlbumPusher(
            items=[self.album],
            service=self.mock_service,
            mappings=mappings
        )
        results = pusher.push()
        self.assertEqual(results[0].status, PushStatus.added)
        self.assertIn("album→track", results[0].message)

    def test_pusher_filtering(self):
        """Test that pusher respects filters."""
        mock_filter = MagicMock()
        mock_filter.should_filter_out.return_value = True
        
        pusher = AlbumPusher(
            items=[self.album],
            service=self.mock_service,
            filter=mock_filter
        )
        results = pusher.push()
        self.assertEqual(results[0].status, PushStatus.filtered)

    def test_pretty_print_result(self):
        """Test pretty_print_result helper."""
        from pushtunes.services.pusher import pretty_print_result
        
        # Test a few statuses
        res1 = PushResult(item=self.album, status=PushStatus.added)
        self.assertIn("Added", pretty_print_result(res1))
        
        res2 = PushResult(item=self.album, status=PushStatus.error)
        self.assertIn("Failed", pretty_print_result(res2))
        
        res3 = PushResult(item=self.album, status=PushStatus.not_found)
        self.assertIn("Could not find", pretty_print_result(res3))

    def test_search_match_strategy(self):
        """Test the basic search matching strategy."""
        strategy = SearchMatchStrategy()
        mock_ops = MagicMock()
        context = MatchContext(
            item=self.album,
            operations=mock_ops,
            service=self.mock_service,
            mappings=None,
            min_similarity=0.8,
            log=MagicMock()
        )
        
        # 1. No search results
        mock_ops.search.return_value = []
        self.assertIsNone(strategy._try_match(context))
        
        # 2. Match found
        match = Album(artists=["Artist"], title="Album")
        mock_ops.search.return_value = [match]
        with patch('pushtunes.services.pusher.get_best_match') as mock_best:
            mock_best.return_value = (match, 1.0)
            res = strategy._try_match(context)
            self.assertEqual(res, match)

    def test_track_pusher_full_flow(self):
        """Test TrackPusher orchestration."""
        self.mock_service.is_track_in_library.return_value = False
        self.mock_service.search_tracks.return_value = [self.track]
        self.mock_service.add_track.return_value = True
        
        pusher = TrackPusher(
            items=[self.track],
            service=self.mock_service
        )
        
        with patch('pushtunes.services.pusher.get_best_match') as mock_best:
            mock_best.return_value = (self.track, 1.0)
            results = pusher.push()
            self.assertEqual(results[0].status, PushStatus.added)

    def test_operations_classes(self):
        """Test AlbumOperations and TrackOperations strategies."""
        from pushtunes.services.pusher import AlbumOperations, TrackOperations
        
        ao = AlbumOperations(self.mock_service)
        ao.is_in_library(self.album)
        self.mock_service.is_album_in_library.assert_called()
        
        to = TrackOperations(self.mock_service)
        to.search(self.track)
        self.mock_service.search_tracks.assert_called()
        
        self.assertEqual(ao.get_service_id_key(), "mock_service_id")
        
        new_track = to.create_item_with_service_id(self.track, "new_id")
        self.assertEqual(new_track.service_id, "new_id")

    def test_pretty_print_more_statuses(self):
        """Test remaining status branches in pretty_print_result."""
        from pushtunes.services.pusher import pretty_print_result
        
        # similarity_too_low
        res = PushResult(item=self.album, status=PushStatus.similarity_too_low)
        self.assertIn("similarity too low", pretty_print_result(res))
        
        # mapped
        res = PushResult(item=self.album, status=PushStatus.mapped, found_item=self.album)
        self.assertIn("Mapped to", pretty_print_result(res))
        
        # deleted
        res = PushResult(item=self.album, status=PushStatus.deleted)
        self.assertIn("Deleted", pretty_print_result(res))

    def test_pusher_add_failure(self):
        """Test behavior when service fails to add a matched item."""
        self.mock_service.is_album_in_library.return_value = False
        self.mock_service.search_albums.return_value = [self.album]
        self.mock_service.add_album.return_value = False # Fails
        
        pusher = AlbumPusher(items=[self.album], service=self.mock_service)
        with patch('pushtunes.services.pusher.get_best_match') as mock_best:
            mock_best.return_value = (self.album, 1.0)
            results = pusher.push()
            self.assertEqual(results[0].status, PushStatus.error)
