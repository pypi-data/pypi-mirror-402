"""Tests for album filtering functionality."""

import unittest
import tempfile
import os
import re
from pushtunes.utils.filters import AlbumFilter, FilterPattern, FilterAction, TrackFilter
from pushtunes.models.album import Album
from pushtunes.models.track import Track


class TestFilterPattern(unittest.TestCase):
    """Test FilterPattern functionality."""

    def test_filter_pattern_creation(self):
        """Test creating filter patterns."""
        pattern = FilterPattern(
            fields={"artist": re.compile(".*dead.*", re.IGNORECASE)},
            action=FilterAction.INCLUDE,
        )
        self.assertIn("artist", pattern.fields)
        self.assertEqual(pattern.fields["artist"].pattern, ".*dead.*")
        self.assertEqual(pattern.action, FilterAction.INCLUDE)


class TestAlbumFilter(unittest.TestCase):
    """Test AlbumFilter functionality."""

    def setUp(self):
        """Set up test albums."""
        self.test_albums = [
            Album.by_single_artist(
                "Dead Can Dance", title="Into the Labyrinth", service_id="1"
            ),
            Album.by_single_artist(
                "Dance with the Dead", title="Send the Signal", service_id="2"
            ),
            Album.by_single_artist("Faith No More", title="Angel Dust", service_id="3"),
            Album.by_single_artist(
                "Metallica", title="Master of Puppets", service_id="4"
            ),
            Album.by_single_artist("The Beatles", title="Abbey Road", service_id="5"),
            Album.by_single_artist(
                "Pink Floyd", title="Dark Side of the Moon", service_id="6"
            ),
            Album.by_single_artist(
                "Dead Can Dance", title="The Serpent's Egg", service_id="7"
            ),
        ]

    def test_empty_filter(self):
        """Test empty filter includes all albums."""
        filter_obj = AlbumFilter()

        for album in self.test_albums:
            self.assertTrue(filter_obj.matches(album))

    def test_empty_filter_summary(self):
        """Test summary for empty filter."""
        filter_obj = AlbumFilter()
        summary = filter_obj.get_summary()
        self.assertEqual(summary, "No filters (all albums included)")


class TestIncludeExcludeFilters(unittest.TestCase):
    """Test new include/exclude filter functionality."""

    def setUp(self):
        """Set up test albums."""
        self.albums = [
            Album.by_single_artist("Taylor Swift", title="1989", service_id="1"),
            Album.by_single_artist("Taylor Swift", title="Reputation", service_id="2"),
            Album.by_single_artist("Opeth", title="Still Life", service_id="3"),
            Album.by_single_artist("Opeth", title="Morningrise", service_id="4"),
            Album.by_single_artist("Volkor X", title="Some Album", service_id="5"),
            Album.by_single_artist("The Beatles", title="Abbey Road", service_id="6"),
        ]

    def test_include_only(self):
        """Test include-only filtering."""
        filter_obj = AlbumFilter()
        filter_obj.add_pattern("artist:'Taylor Swift'", FilterAction.INCLUDE)

        filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

        # Should only include Taylor Swift albums
        self.assertEqual(len(filtered), 2)
        for album in filtered:
            self.assertEqual(album.artist, "Taylor Swift")

    def test_exclude_only(self):
        """Test exclude-only filtering."""
        filter_obj = AlbumFilter()
        filter_obj.add_pattern("artist:'Volkor X'", FilterAction.EXCLUDE)

        filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

        # Should include everything except Volkor X
        self.assertEqual(len(filtered), 5)
        artists = [a.artist for a in filtered]
        self.assertNotIn("Volkor X", artists)
        self.assertIn("Taylor Swift", artists)
        self.assertIn("Opeth", artists)

    def test_include_and_exclude(self):
        """Test combined include and exclude patterns."""
        filter_obj = AlbumFilter()
        filter_obj.add_pattern("artist:'Opeth'", FilterAction.INCLUDE)
        filter_obj.add_pattern("artist:'Opeth' album:'Still Life'", FilterAction.EXCLUDE)

        filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

        # Should include Opeth albums except Still Life
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].artist, "Opeth")
        self.assertEqual(filtered[0].title, "Morningrise")

    def test_and_logic_within_pattern(self):
        """Test AND logic within a single pattern."""
        filter_obj = AlbumFilter()
        # This should only match albums by Taylor Swift with title containing "198"
        filter_obj.add_pattern("artist:'Taylor Swift' album:'.*198.*'", FilterAction.INCLUDE)

        filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

        # Should only match "1989"
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "1989")

    def test_from_patterns_file(self):
        """Test loading patterns from file with +/- prefixes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("+ artist:'Taylor Swift'\n")
            f.write("- artist:'Volkor X'\n")
            f.write("+ artist:'Opeth' album:'Morningrise'\n")
            f.write("- artist:'Opeth' album:'Still Life'\n")
            f.write("# This is a comment\n")
            f.write("\n")
            temp_file = f.name

        try:
            filter_obj = AlbumFilter.from_patterns_file(temp_file)

            # Check that we have 4 patterns
            self.assertEqual(len(filter_obj.patterns), 4)

            # Apply filter
            filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

            # Should include: Taylor Swift (both albums), Opeth Morningrise
            # Should exclude: Volkor X, Opeth Still Life, The Beatles
            artists_titles = [(a.artist, a.title) for a in filtered]

            self.assertIn(("Taylor Swift", "1989"), artists_titles)
            self.assertIn(("Taylor Swift", "Reputation"), artists_titles)
            self.assertIn(("Opeth", "Morningrise"), artists_titles)
            self.assertNotIn(("Opeth", "Still Life"), artists_titles)
            self.assertNotIn(("Volkor X", "Some Album"), artists_titles)
            self.assertNotIn(("The Beatles", "Abbey Road"), artists_titles)

        finally:
            os.unlink(temp_file)

    def test_multiple_includes_or_logic(self):
        """Test that multiple include patterns use OR logic."""
        filter_obj = AlbumFilter()
        filter_obj.add_pattern("artist:'Taylor Swift'", FilterAction.INCLUDE)
        filter_obj.add_pattern("artist:'Opeth'", FilterAction.INCLUDE)

        filtered = [a for a in self.albums if not filter_obj.should_filter_out(a)]

        # Should include all Taylor Swift and Opeth albums
        self.assertEqual(len(filtered), 4)
        artists = set(a.artist for a in filtered)
        self.assertEqual(artists, {"Taylor Swift", "Opeth"})

    def test_exclude_overrides_include(self):
        """Test that exclude patterns override includes (include-first logic)."""
        filter_obj = AlbumFilter()
        filter_obj.add_pattern("artist:'Opeth'", FilterAction.INCLUDE)
        filter_obj.add_pattern("artist:'Opeth' album:'Still Life'", FilterAction.EXCLUDE)

        # Test both Opeth albums
        still_life = [a for a in self.albums if a.title == "Still Life"][0]
        morningrise = [a for a in self.albums if a.title == "Morningrise"][0]

        # Still Life should be filtered out despite matching the include
        self.assertTrue(filter_obj.should_filter_out(still_life))
        # Morningrise should pass
        self.assertFalse(filter_obj.should_filter_out(morningrise))


class TestTrackFilter(unittest.TestCase):
    """Test TrackFilter functionality."""

    def test_track_field_pattern(self):
        """Test filtering by track field."""
        tf = TrackFilter()
        tf.add_pattern("track:'Bohemian Rhapsody'")
        
        t1 = Track(artists=["Queen"], title="Bohemian Rhapsody")
        t2 = Track(artists=["Queen"], title="Killer Queen")
        
        self.assertTrue(tf.matches(t1))
        self.assertFalse(tf.matches(t2))

    def test_track_album_filter(self):
        """Test filtering by track album field."""
        tf = TrackFilter()
        tf.add_pattern("album:'Opera'")
        
        t1 = Track(artists=["Queen"], title="Bohemian Rhapsody", album="A Night at the Opera")
        t2 = Track(artists=["Queen"], title="Killer Queen", album="Sheer Heart Attack")
        
        self.assertTrue(tf.matches(t1))
        self.assertFalse(tf.matches(t2))

    def test_track_from_patterns_file(self):
        """Test TrackFilter from file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("+ artist:'Opeth' track:'Deliverance'\n")
            temp_path = f.name
        try:
            tf = TrackFilter.from_patterns_file(temp_path)
            t1 = Track(artists=["Opeth"], title="Deliverance")
            t2 = Track(artists=["Opeth"], title="Ghost of Perdition")
            self.assertTrue(tf.matches(t1))
            self.assertFalse(tf.matches(t2))
        finally:
            os.unlink(temp_path)

    def test_legacy_matches_or_logic(self):
        """Test that matches() uses OR logic when all patterns are INCLUDE."""
        af = AlbumFilter()
        af.add_pattern("artist:'Pink Floyd'")
        af.add_pattern("artist:'Daft Punk'")
        
        # Should match either
        self.assertTrue(af.matches(Album(artists=["Pink Floyd"], title="T")))
        self.assertTrue(af.matches(Album(artists=["Daft Punk"], title="T")))
        self.assertFalse(af.matches(Album(artists=["Queen"], title="T")))

    def test_get_summary(self):
        af = AlbumFilter()
        af.add_pattern("artist:'A'", FilterAction.INCLUDE)
        af.add_pattern("album:'B'", FilterAction.EXCLUDE)
        summary = af.get_summary()
        self.assertIn("Include: artist:'A'", summary)
        self.assertIn("Exclude: album:'B'", summary)

    def test_track_matches_logic(self):
        tf = TrackFilter()
        tf.add_pattern("artist:'A'", FilterAction.INCLUDE)
        
        # Test should_filter_out logic for tracks
        t1 = Track(artists=["A"], title="T")
        t2 = Track(artists=["B"], title="T")
        self.assertFalse(tf.should_filter_out(t1))
        self.assertTrue(tf.should_filter_out(t2))

    def test_filter_utils(self):
        af = AlbumFilter()
        self.assertFalse(bool(af))
        self.assertEqual(len(af), 0)
        
        af.add_pattern("artist:'A'")
        self.assertTrue(bool(af))
        self.assertEqual(len(af), 1)
        
        tf = TrackFilter()
        tf.add_pattern("track:'T'")
        self.assertIn("track:'T'", tf.get_summary())


if __name__ == "__main__":
    unittest.main()
