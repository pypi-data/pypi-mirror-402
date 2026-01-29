"""Abstract base classes for pushtunes services."""

from abc import ABC, abstractmethod

from pushtunes.models.album import Album
from pushtunes.models.track import Track
from pushtunes.utils.cache_manager import CacheManager
from pushtunes.utils.logging import get_logger


class MusicService(ABC):
    """Base class for music services (e.g., Spotify, YouTube Music)."""

    log = get_logger()
    service_name: str

    def __init__(self):
        """Initialize service with cache manager.

        Subclasses should call super().__init__() after setting self.service_name
        """
        self.cache = CacheManager(
            self.service_name, self.get_library_albums, self.get_library_tracks
        )

    @abstractmethod
    def search_albums(self, album: Album) -> list[Album]:
        pass

    @abstractmethod
    def is_album_in_library(self, album: Album) -> bool:
        pass

    @abstractmethod
    def add_album(self, album: Album) -> bool:
        pass

    @abstractmethod
    def search_tracks(self, track: Track) -> list[Track]:
        pass

    @abstractmethod
    def is_track_in_library(self, track: Track) -> bool:
        pass

    @abstractmethod
    def add_track(self, track: Track) -> bool:
        pass

    @abstractmethod
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: list[str]) -> bool:
        pass

    @abstractmethod
    def remove_album(self, album: Album) -> bool:
        """Remove an album from the user's library.

        Args:
            album: Album to remove (must have service_id set)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def remove_track(self, track: Track) -> bool:
        """Remove a track from the user's library.

        Args:
            track: Track to remove (must have service_id set)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_user_playlists(self) -> list[dict]:
        """Get all playlists owned by the current user.

        Returns:
            List of playlist dictionaries with 'id' and 'name' keys
        """
        pass

    @abstractmethod
    def create_playlist(self, name: str, description: str = "") -> str | None:
        """Create a new playlist.

        Args:
            name: Playlist name
            description: Playlist description (optional)

        Returns:
            Playlist ID if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> list[Track]:
        """Get all tracks from a playlist.

        Args:
            playlist_id: ID of the playlist

        Returns:
            List of Track objects
        """
        pass

    @abstractmethod
    def replace_playlist_tracks(self, playlist_id: str, track_ids: list[str]) -> bool:
        """Replace all tracks in a playlist.

        Args:
            playlist_id: ID of the playlist
            track_ids: List of track IDs to replace with

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def remove_tracks_from_playlist(self, playlist_id: str, track_ids: list[str]) -> bool:
        """Remove tracks from a playlist.

        Args:
            playlist_id: ID of the playlist
            track_ids: List of track IDs to remove

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_library_albums(self) -> list[Album]:
        """Returns all albums in a user's library.

        Returns:
            List of Album objects.
        """
        pass

    @abstractmethod
    def get_library_tracks(self) -> list[Track]:
        """Returns all tracks in a user's library.

        Returns:
            List of Track objects.
        """
        pass
