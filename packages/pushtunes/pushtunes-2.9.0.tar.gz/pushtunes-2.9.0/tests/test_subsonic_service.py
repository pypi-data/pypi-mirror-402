import os
from unittest.mock import MagicMock, patch

import pytest

from pushtunes.services.subsonic import SubsonicService
from pushtunes.models.track import Track


@pytest.fixture
def mock_subsonic_client():
    """Fixture for a mocked SubsonicClient."""
    # We patch the class, so any instance created will be a mock
    with patch('pushtunes.services.subsonic.SubsonicClient') as mock_client_class:
        # This is the instance that will be used in SubsonicService
        mock_client_instance = mock_client_class.return_value

        # --- Mock setup for get_library_tracks ---

        # 1. mock_client_instance.get_albums() returns a list of album dicts
        mock_client_instance.get_albums.return_value = [
            {"id": "album-1", "artist": "Artist 1", "title": "Album 1", "year": 2023},
        ]

        # 2. mock_client_instance.connection.get_album() returns a mock album object
        mock_album_obj = MagicMock()

        # The album object has a 'song' attribute which is a list of song objects
        song_from_album_1 = MagicMock()
        song_from_album_1.id = 'track-1'
        song_from_album_1.artist = 'Artist 1'
        song_from_album_1.title = 'Track 1'
        song_from_album_1.album = 'Album 1'
        song_from_album_1.year = 2023
        # The _subsonic_track_to_track method uses .get()
        song_from_album_1.get.side_effect = lambda key, default='': getattr(song_from_album_1, key, default)

        song_from_album_2 = MagicMock()
        song_from_album_2.id = 'track-2'
        song_from_album_2.artist = 'Artist 1'
        song_from_album_2.title = 'Track 2'
        song_from_album_2.album = 'Album 1'
        song_from_album_2.year = 2023
        song_from_album_2.get.side_effect = lambda key, default='': getattr(song_from_album_2, key, default)

        mock_album_obj.song = [song_from_album_1, song_from_album_2]

        mock_client_instance.connection.get_album.return_value = mock_album_obj

        # 3. mock_client_instance.connection.search3() returns a mock search result object
        mock_search_result_obj = MagicMock()

        # The search result object has a 'song' attribute which is a list of song objects
        standalone_song = MagicMock()
        standalone_song.id = 'track-3'
        standalone_song.artist = 'Artist 2'
        standalone_song.title = 'Track 3 (Single)'
        standalone_song.album = None
        standalone_song.year = 2024
        standalone_song.get.side_effect = lambda key, default='': getattr(standalone_song, key, default)

        # Add a song that's already in an album to test deduplication
        song_already_in_album = MagicMock()
        song_already_in_album.id = 'track-1'  # same id as song_from_album_1
        # Make sure get returns the id
        song_already_in_album.get.side_effect = lambda key, default='': getattr(song_already_in_album, key, default)


        mock_search_result_obj.song = [standalone_song, song_already_in_album]

        mock_client_instance.connection.search3.return_value = mock_search_result_obj

        yield mock_client_instance


@pytest.fixture
def subsonic_service(mock_subsonic_client):
    """Fixture for SubsonicService with mocked client."""
    # Set dummy credentials to pass the validation in __init__
    os.environ['SUBSONIC_URL'] = 'http://dummy.url'
    os.environ['SUBSONIC_USER'] = 'dummy'
    os.environ['SUBSONIC_PASS'] = 'dummy'

    service = SubsonicService()

    # Clean up env vars after test
    yield service
    del os.environ['SUBSONIC_URL']
    del os.environ['SUBSONIC_USER']
    del os.environ['SUBSONIC_PASS']


def test_get_library_tracks(subsonic_service, mock_subsonic_client):
    """Test get_library_tracks with object-based responses from py-opensubsonic."""
    # Disable the progress bar for testing
    with patch('sys.stdout.isatty', return_value=False):
        tracks = subsonic_service.get_library_tracks()

    # Expected: 2 tracks from album + 1 standalone track.
    # The duplicate track with id 'track-1' from search should be ignored.
    assert len(tracks) == 3

    # Check track from album
    track1 = tracks[0]
    assert isinstance(track1, Track)
    assert track1.service_id == 'track-1'
    assert track1.artists == ['Artist 1']
    assert track1.title == 'Track 1'
    assert track1.album == 'Album 1'
    assert track1.year == 2023

    # Check standalone track from search
    track3 = tracks[2]
    assert isinstance(track3, Track)
    assert track3.service_id == 'track-3'
    assert track3.artists == ['Artist 2']
    assert track3.title == 'Track 3 (Single)'
    assert track3.album is None
    assert track3.year == 2024

    # Verify that the correct client methods were called
    mock_subsonic_client.get_albums.assert_called_once()
    mock_subsonic_client.connection.get_album.assert_called_once_with('album-1')
    mock_subsonic_client.connection.search3.assert_called_once_with(query='', song_count=10000)
