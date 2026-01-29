"""Tests for CLI shared utilities."""

import unittest
from unittest.mock import patch
from pushtunes.utils.cli.commands.shared import create_source, create_service, print_stats, print_compare_stats


class TestCliShared(unittest.TestCase):
    """Test CLI shared logic."""

    @patch("pushtunes.utils.cli.commands.shared.SubsonicSource")
    def test_create_source_subsonic(self, mock_sub):
        config = {"subsonic_url": "http://test", "subsonic_username": "u", "subsonic_password": "p"}
        create_source("subsonic", config)
        mock_sub.assert_called_with(url="http://test", username="u", password="p", port=443)

    @patch("pushtunes.utils.cli.commands.shared.CSVSource")
    def test_create_source_csv(self, mock_csv):
        config = {"csv_file": "test.csv"}
        create_source("csv", config)
        mock_csv.assert_called_with(csv_file="test.csv")

    def test_create_source_unsupported(self):
        with self.assertRaises(ValueError):
            create_source("invalid", {})

    @patch("pushtunes.utils.cli.commands.shared.SpotifyService")
    def test_create_service_spotify(self, mock_sp):
        config = {"similarity": 0.9}
        create_service("spotify", config)
        # Note: it also passes client_id etc from config.get
        mock_sp.assert_called()

    def test_print_stats(self):
        stats = {
            "total": 10, "added": 5, "skipped_existing": 3, 
            "skipped_not_found": 1, "skipped_low_similarity": 1, "errors": 0
        }
        with patch("builtins.print") as mock_print:
            print_stats(stats, "albums")
            mock_print.assert_called()

    def test_print_compare_stats(self):
        stats = {"total": 5, "in_both": 2, "only_in_source": 2, "only_in_target": 1}
        with patch("builtins.print") as mock_print:
            print_compare_stats(stats, "tracks")
            mock_print.assert_called()
