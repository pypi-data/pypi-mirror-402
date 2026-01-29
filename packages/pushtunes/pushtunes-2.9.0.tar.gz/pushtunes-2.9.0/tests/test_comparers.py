"""Tests for AlbumComparer and TrackComparer services."""

import unittest
from unittest.mock import MagicMock
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.models.compare_status import CompareStatus
from pushtunes.services.album_comparer import AlbumComparer
from pushtunes.services.track_comparer import TrackComparer
from pushtunes.utils.filters import AlbumFilter, FilterAction


class TestAlbumComparer(unittest.TestCase):
    """Test AlbumComparer logic."""

    def setUp(self):
        self.album1 = Album(artists=["Pink Floyd"], title="The Wall", year=1979)
        self.album2 = Album(artists=["Daft Punk"], title="Discovery", year=2001)
        self.album3 = Album(artists=["Lorn"], title="Vessel", year=2015)

    def test_compare_perfect_match(self):
        """Test matching identical albums."""
        comparer = AlbumComparer(
            albums_source=[self.album1],
            albums_target=[self.album1]
        )
        results = comparer.compare_albums()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CompareStatus.in_both)
        self.assertEqual(results[0].album, self.album1)
        self.assertEqual(results[0].matched_album, self.album1)

    def test_compare_only_in_source(self):
        """Test album only in source library."""
        comparer = AlbumComparer(
            albums_source=[self.album1],
            albums_target=[]
        )
        results = comparer.compare_albums()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CompareStatus.only_in_source)
        self.assertEqual(results[0].album, self.album1)

    def test_compare_only_in_target(self):
        """Test album only in target library."""
        comparer = AlbumComparer(
            albums_source=[],
            albums_target=[self.album1]
        )
        results = comparer.compare_albums()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CompareStatus.only_in_target)
        self.assertEqual(results[0].album, self.album1)

    def test_compare_with_filter(self):
        """Test that filtered albums are marked correctly."""
        album_filter = AlbumFilter()
        # The comparer uses filter.matches(album) which returns True if it SHOULD be processed
        # and False if it should be FILTERED.
        # But wait, looking at album_comparer.py:
        # if self.filter and self.filter.matches(album):
        #     add_result(..., status=CompareStatus.filtered)
        # So matches() returning True means it IS filtered.
        album_filter.add_pattern("artist:'Pink Floyd'", FilterAction.INCLUDE)
        
        comparer = AlbumComparer(
            albums_source=[self.album1, self.album2],
            albums_target=[self.album1, self.album2],
            filter=album_filter
        )
        results = comparer.compare_albums()
        
        # Result for album1 (matches pattern, so filtered)
        res1 = next(r for r in results if r.album == self.album1)
        self.assertEqual(res1.status, CompareStatus.filtered)
        
        # Result for album2 (doesn't match pattern, so in_both)
        res2 = next(r for r in results if r.album == self.album2)
        self.assertEqual(res2.status, CompareStatus.in_both)

    def test_compare_with_mappings(self):
        """Test matching using MappingsManager."""
        # album1 and album3 are different, but we'll map them
        mappings = MagicMock()
        mappings.get_album_mapping.return_value = self.album3
        
        comparer = AlbumComparer(
            albums_source=[self.album1],
            albums_target=[self.album3],
            mappings=mappings
        )
        results = comparer.compare_albums()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CompareStatus.in_both)
        self.assertEqual(results[0].matched_album, self.album3)
        mappings.get_album_mapping.assert_called_with(self.album1, "target")

    def test_similarity_threshold(self):
        """Test that similarity threshold affects matching."""
        # Slightly different titles
        source_album = Album(artists=["Artist"], title="The Great Album")
        target_album = Album(artists=["Artist"], title="Great Album", service_id="123")
        
        # High similarity required - should fail
        comparer = AlbumComparer(
            albums_source=[source_album],
            albums_target=[target_album],
            min_similarity=0.99
        )
        results = comparer.compare_albums()
        # Should be only_in_source because similarity is too low
        self.assertEqual(results[0].status, CompareStatus.only_in_source)
        
        # Low similarity required - should match
        comparer.min_similarity = 0.5
        results = comparer.compare_albums()
        res = next(r for r in results if r.album == source_album and r.status != CompareStatus.only_in_target)
        self.assertEqual(res.status, CompareStatus.in_both)


class TestTrackComparer(unittest.TestCase):
    """Test TrackComparer logic."""

    def setUp(self):
        self.track1 = Track(artists=["Queen"], title="Bohemian Rhapsody", album="A Night at the Opera")
        self.track2 = Track(artists=["Led Zeppelin"], title="Stairway to Heaven", album="Led Zeppelin IV")

    def test_compare_tracks_basic(self):
        """Test basic track matching."""
        comparer = TrackComparer(
            tracks_source=[self.track1, self.track2],
            tracks_target=[self.track1]
        )
        results = comparer.compare_tracks()
        
        # track1 should be in both
        res1 = next(r for r in results if r.track == self.track1)
        self.assertEqual(res1.status, CompareStatus.in_both)
        
        # track2 should be only in source
        res2 = next(r for r in results if r.track == self.track2)
        self.assertEqual(res2.status, CompareStatus.only_in_source)

    def test_compare_tracks_with_mappings(self):
        """Test matching tracks using MappingsManager."""
        mapped_track = Track(artists=["Artist X"], title="Track X")
        mappings = MagicMock()
        mappings.get_track_mapping.return_value = mapped_track
        
        comparer = TrackComparer(
            tracks_source=[self.track1],
            tracks_target=[mapped_track],
            mappings=mappings
        )
        results = comparer.compare_tracks()
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, CompareStatus.in_both)
        self.assertEqual(results[0].matched_track, mapped_track)
