"""Tests for reporting utility."""

import unittest
from unittest.mock import patch
from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.models.push_status import PushStatus
from pushtunes.services.pusher import PushResult
from pushtunes.utils.reporting import generate_report, print_album_results_table


class TestReporting(unittest.TestCase):
    """Test reporting logic."""

    def setUp(self):
        self.album = Album(artists=["Pink Floyd"], title="The Wall", year=1979)
        self.track = Track(artists=["Queen"], title="Bohemian Rhapsody", album="A Night at the Opera")
        
        self.album_result = PushResult(item=self.album, status=PushStatus.not_found)
        self.track_result = PushResult(item=self.track, status=PushStatus.added)

    def test_print_album_results_table(self):
        """Test print_album_results_table runs without error."""
        results = [self.album_result]
        with patch('rich.console.Console.print'):
            print_album_results_table(results, "not_found", "Not Found", use_color=False)

    def test_generate_report_album(self):
        """Test generate_report for albums."""
        results = [self.album_result]
        with patch('rich.console.Console.print'):
            generate_report(results, ["not_found"], result_type="album", use_color=False)

    def test_generate_report_track(self):
        """Test generate_report for tracks."""
        results = [self.track_result]
        with patch('rich.console.Console.print'):
            generate_report(results, ["added"], result_type="track", use_color=False)

    def test_generate_report_playlist(self):
        """Test generate_report for playlists."""
        # Playlist uses matched status
        from pushtunes.services.playlist_pusher import TrackMatchResult
        res = TrackMatchResult(source_track=self.track, status=PushStatus.matched)
        with patch('rich.console.Console.print'):
            generate_report([res], ["matched"], result_type="playlist", use_color=False)

    def test_generate_report_unknown_status(self):
        """Test generate_report with unknown status."""
        results = [self.album_result]
        with patch('rich.console.Console.print') as mock_print:
            generate_report(results, ["invalid_status"], result_type="album", use_color=False)
            # Should mention warning
            calls = [c[0][0] for c in mock_print.call_args_list if isinstance(c[0][0], str)]
            self.assertTrue(any("Unknown status" in s for s in calls))

    def test_generate_report_empty(self):
        """Test generate_report with empty inputs."""
        # Should return early
        generate_report([], ["not_found"])
        generate_report([self.album_result], [])
