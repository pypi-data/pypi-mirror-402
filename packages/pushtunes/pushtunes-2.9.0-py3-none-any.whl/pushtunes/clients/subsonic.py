import os

import libopensonic

from pushtunes.utils.logging import get_logger

class SubsonicClient:
    """Client for interacting with Subsonic music server"""

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int = 443,
    ):
        """Initialize Subsonic client with connection parameters

        Args:
            url: Subsonic server URL (defaults to SUBSONIC_URL env var)
            username: Username (defaults to SUBSONIC_USER env var)
            password: Password (defaults to SUBSONIC_PASS env var)
            port: Server port (defaults to 443)
        """
        self.url: str | None = url or os.getenv("SUBSONIC_URL")
        self.username: str | None = username or os.getenv("SUBSONIC_USER")
        self.password: str | None = password or os.getenv("SUBSONIC_PASS")
        self.port: int = port

        self.connection: libopensonic.Connection = libopensonic.Connection(
            str(self.url) if self.url else "",
            str(self.username) if self.username else "",
            str(self.password) if self.password else "",
            port=self.port,
        )

        self.log = get_logger()

    def get_albums(self, albums=None, offset=0, progress_bar=None, progress_task=None):
        """Fetch all albums from Subsonic server

        Args:
            albums: Existing list of albums to append to (for recursion)
            offset: Pagination offset
            progress_bar: Optional Progress object for displaying progress
            progress_task: Optional task ID for updating progress

        Returns:
            List of album dictionaries with 'artist', 'title', 'id', and 'year' keys
        """
        if albums is None:
            albums = []

        # py-opensonic: get_album_list2 returns list of album objects directly
        albumlist = self.connection.get_album_list2(
            "alphabeticalByArtist", size=500, offset=offset
        )

        for entry in albumlist:
            if not (
                entry.name == "[Unknown Album]"
                or entry.artist == "[Unknown Artist]"
            ):
                album_id = entry.id
                album_year = entry.year
                albums.append(
                    {
                        "id": album_id,
                        "artist": entry.artist,
                        "title": entry.name,
                        "year": album_year,
                    }
                )

                # Update progress if provided
                if progress_bar and progress_task is not None:
                    progress_bar.update(progress_task, advance=1)

        if len(albumlist) == 500:
            # Make a recursive call to fetch more albums
            additional_albums = self.get_albums(
                None, offset + 500, progress_bar, progress_task
            )
            albums.extend(additional_albums)

        return albums

    def get_tracks(self, tracks=None, offset=0):
        """Fetch all starred/favorite tracks from Subsonic server

        Args:
            tracks: Existing list of tracks to append to (for recursion)
            offset: Pagination offset

        Returns:
            List of track dictionaries with 'artist', 'title', 'album', 'year' keys
        """
        if tracks is None:
            tracks = []

        starred = self.connection.get_starred2()
        if not hasattr(starred, 'song') or not starred.song:
            return tracks

        song_entries = starred.song
        # Handle single song as dict vs list
        if isinstance(song_entries, dict):
            song_entries = [song_entries]

        for entry in song_entries:
            self.log.info(
                f"Fetching Subsonic metadata for {getattr(entry, 'artist', 'Unknown')} - {getattr(entry, 'title', 'Unknown')}"
            )

            # Skip unknown tracks
            entry_title = getattr(entry, 'title', '[Unknown]')
            entry_artist = getattr(entry, 'artist', '[Unknown Artist]')
            if entry_title == "[Unknown]" or entry_artist == "[Unknown Artist]":
                continue

            track_year = None
            if hasattr(entry, 'year'):
                try:
                    year_val = getattr(entry, 'year')
                    if year_val is not None:
                        track_year = int(str(year_val))
                except (ValueError, TypeError):
                    pass

            tracks.append(
                {
                    "artist": getattr(entry, 'artist', ''),
                    "title": getattr(entry, 'title', ''),
                    "album": getattr(entry, 'album', None),
                    "year": track_year,
                }
            )

        return tracks

    def get_playlists(self):
        """Fetch all playlists from Subsonic server

        Returns:
            List of playlist dictionaries with 'id' and 'name' keys
        """
        playlists = []
        raw_playlists = self.connection.get_playlists()
        for rp in raw_playlists:
            playlists.append(
                {
                    "id" : rp.id,
                    "name" : rp.name,
                    "song_count" : rp.song_count
                }
            )
        return playlists

    def get_playlist(self, playlist_id):
        """Fetch a specific playlist by ID

        Args:
            playlist_id: ID of the playlist to fetch

        Returns:
            Playlist dictionary with 'name' and 'entry' keys
        """
        # py-opensonic: get_playlist returns playlist object directly
        playlist = self.connection.get_playlist(playlist_id)
        if not playlist:
            return None

        # Convert object to dict for backwards compatibility
        playlist_dict = {
            "id": getattr(playlist, 'id', None),
            "name": getattr(playlist, 'name', ''),
        }

        # Handle case where there are no entries in the playlist
        if playlist.song_count == 0:
            playlist_dict["entry"] = []
        else:
            playlist_dict["entry"] = playlist.entry

        return playlist_dict

    def create_playlist(self, name: str) -> str | None:
        """Create a new playlist.

        Args:
            name: Name of the playlist to create

        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            # py-opensonic: create_playlist returns playlist object directly
            playlist = self.connection.create_playlist(name=name)
            if playlist and hasattr(playlist, 'id'):
                return playlist.id
            return None
        except Exception as e:
            self.log.error(f"Error creating playlist '{name}': {e}")
            return None

    def update_playlist(self, playlist_id: str, track_ids: list[str]) -> bool:
        """Replace all tracks in a playlist with the provided track IDs.

        Args:
            playlist_id: ID of the playlist to update
            track_ids: List of track IDs to set as the playlist content

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current playlist to find number of tracks
            playlist = self.get_playlist(playlist_id)
            if not playlist:
                self.log.error(f"Playlist {playlist_id} not found")
                return False

            current_track_count = len(playlist.get("entry", []))

            # Remove all existing tracks by index (from end to start to avoid index shifting)
            if current_track_count > 0:
                indices_to_remove = list(range(current_track_count))
                self.connection.update_playlist(
                    lid=playlist_id, song_indices_to_remove=indices_to_remove
                )

            # Add new tracks
            if track_ids:
                self.connection.update_playlist(lid=playlist_id, song_ids_to_add=track_ids)

            return True
        except Exception as e:
            self.log.error(f"Error updating playlist {playlist_id}: {e}")
            return False

    def add_to_playlist(self, playlist_id: str, track_ids: list[str]) -> bool:
        """Add tracks to the end of a playlist.

        Args:
            playlist_id: ID of the playlist
            track_ids: List of track IDs to add

        Returns:
            True if successful, False otherwise
        """
        try:
            self.connection.update_playlist(lid=playlist_id, song_ids_to_add=track_ids)
            return True
        except Exception as e:
            self.log.error(f"Error adding tracks to playlist {playlist_id}: {e}")
            return False

    def remove_from_playlist(self, playlist_id: str, indices: list[int]) -> bool:
        """Remove tracks at specific indices from a playlist.

        Args:
            playlist_id: ID of the playlist
            indices: List of track indices to remove (0-based)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.connection.update_playlist(
                lid=playlist_id, song_indices_to_remove=indices
            )
            return True
        except Exception as e:
            self.log.error(f"Error removing tracks from playlist {playlist_id}: {e}")
            return False

    def get_all_tracks(self, limit: int | None = None) -> list[dict]:
        """Fetch all tracks from the Subsonic server (not just starred).

        Args:
            limit: Optional limit on number of tracks to fetch

        Returns:
            List of track dictionaries
        """
        all_tracks = []

        try:
            # Get all albums first
            albums = self.get_albums()

            for album_info in albums:
                # Get album details with tracks
                try:
                    # Use a simpler approach: get random albums and their songs
                    # py-opensonic: get_album_list2 returns list of album objects directly
                    random_albums = self.connection.get_album_list2("random", size=500)

                    for album in random_albums:
                        album_id = album.id
                        # py-opensonic: get_album returns album object directly
                        album_details = self.connection.get_album(album_id)

                        if hasattr(album_details, 'song') and album_details.song:
                            songs = album_details.song
                            if isinstance(songs, dict):
                                songs = [songs]

                            all_tracks.extend(songs)

                            if limit and len(all_tracks) >= limit:
                                return all_tracks[:limit]

                    break  # Just do one pass for now

                except Exception as e:
                    self.log.warning(f"Error fetching tracks: {e}")
                    continue

        except Exception as e:
            self.log.error(f"Error fetching all tracks: {e}")

        return all_tracks