from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from pushtunes.models.album import Album
from pushtunes.models.push_status import PushStatus
from pushtunes.models.track import Track
from pushtunes.services.mappings_manager import MappingsManager
from pushtunes.services.music_service import MusicService
from pushtunes.utils.filters import AlbumFilter, TrackFilter
from pushtunes.utils.logging import get_logger
from pushtunes.utils.similarity import get_best_match

# Type variable constrained to Album or Track
# This allows us to write generic code that works with either type while maintaining
# type safety. The type checker understands that T will be consistently either Album
# or Track throughout a generic class instance.
#
# Note: Some `type: ignore` comments are needed where we perform runtime isinstance
# checks on T. The type checker cannot narrow generic type variables based on isinstance,
# even though the runtime logic is correct. These are documented inline.
T = TypeVar("T", Album, Track)


@dataclass(frozen=True, slots=True)
class PushResult(Generic[T]):
    """Result of pushing a single item"""

    item: T
    status: PushStatus
    message: str = ""
    found_item: T | None = None


# ============================================================================
# Item Operations - Strategy Pattern for type-specific operations
# ============================================================================


class ItemOperations(ABC, Generic[T]):
    """Abstract strategy for item-specific operations"""

    def __init__(self, service: MusicService):
        self.service = service

    @abstractmethod
    def is_in_library(self, item: T) -> bool:
        """Check if item is in library"""
        pass

    @abstractmethod
    def search(self, item: T) -> list[T]:
        """Search for item on service"""
        pass

    @abstractmethod
    def add(self, item: T) -> bool:
        """Add item to library"""
        pass

    @abstractmethod
    def get_service_id_key(self) -> str:
        """Get the key name for service ID in extra_data"""
        pass

    @abstractmethod
    def create_item_with_service_id(self, item: T, service_id: str) -> T:
        """Create a new item instance with service ID"""
        pass


class AlbumOperations(ItemOperations[Album]):
    """Concrete strategy for album operations"""

    def is_in_library(self, item: Album) -> bool:
        return self.service.is_album_in_library(item)

    def search(self, item: Album) -> list[Album]:
        return self.service.search_albums(item)

    def add(self, item: Album) -> bool:
        return self.service.add_album(item)

    def get_service_id_key(self) -> str:
        return f"{self.service.service_name}_id"

    def create_item_with_service_id(self, item: Album, service_id: str) -> Album:
        return Album(
            artists=item.artists,
            title=item.title,
            year=item.year,
            service_id=service_id,
            service_name=self.service.service_name,
        )


class TrackOperations(ItemOperations[Track]):
    """Concrete strategy for track operations"""

    def is_in_library(self, item: Track) -> bool:
        return self.service.is_track_in_library(item)

    def search(self, item: Track) -> list[Track]:
        return self.service.search_tracks(item)

    def add(self, item: Track) -> bool:
        return self.service.add_track(item)

    def get_service_id_key(self) -> str:
        return f"{self.service.service_name}_id"

    def create_item_with_service_id(self, item: Track, service_id: str) -> Track:
        return Track(
            artists=item.artists,
            title=item.title,
            album=item.album,
            year=item.year,
            service_id=service_id,
            service_name=self.service.service_name,
        )


# ============================================================================
# Match Strategies - Chain of Responsibility for finding matches
# ============================================================================


@dataclass
class MatchContext(Generic[T]):
    """Context passed through the match chain"""

    item: T
    operations: ItemOperations[T]
    service: MusicService
    mappings: MappingsManager | None
    min_similarity: float
    log: Any


class MatchStrategy(ABC, Generic[T]):
    """Base class for match strategies (Chain of Responsibility)"""

    def __init__(self, next_strategy: "MatchStrategy[T] | None" = None):
        self.next_strategy = next_strategy

    def find_match(self, context: MatchContext[T]) -> T | None:
        """Try to find a match, delegate to next strategy if unsuccessful"""
        match = self._try_match(context)
        if match:
            return match
        if self.next_strategy:
            return self.next_strategy.find_match(context)
        return None

    @abstractmethod
    def _try_match(self, context: MatchContext[T]) -> T | None:
        """Attempt to find a match using this strategy"""
        pass


class ServiceIdMatchStrategy(MatchStrategy[T]):
    """Try to match using service ID from CSV extra_data"""

    def _try_match(self, context: MatchContext[T]) -> T | None:
        if not context.item.extra_data:
            return None

        service_id_key = context.operations.get_service_id_key()
        service_id = context.item.extra_data.get(service_id_key)

        if service_id:
            match = context.operations.create_item_with_service_id(
                context.item, service_id
            )
            context.log.info(
                f"Using CSV service_id for {context.item.artist} - {context.item.title} "
                f"-> {context.service.service_name} ID {service_id}"
            )
            return match

        return None


class MappingMatchStrategy(MatchStrategy[T]):
    """Try to match using mappings (handles same-type mappings only)"""

    def _try_match(self, context: MatchContext[T]) -> T | None:
        if not context.mappings:
            return None

        item = context.item
        service_name = context.service.service_name
        service_client = self._get_service_client(context)

        # Get the appropriate mapping - type checker can't narrow T based on isinstance
        # but we know at runtime this is safe
        if isinstance(item, Album):
            mapped_result = context.mappings.get_album_mapping(
                item, service_name, service_client
            )
        elif isinstance(item, Track):
            mapped_result = context.mappings.get_track_mapping(
                item, service_name, service_client
            )
        else:
            return None

        if not mapped_result:
            return None

        # Check for cross-type mapping (handled separately in ItemProcessor)
        if type(mapped_result) is not type(item):
            return None

        # At this point we know mapped_result matches T, but type checker can't prove it
        # Safe to cast since we checked type(mapped_result) == type(item)
        mapped_item: T = mapped_result  # type: ignore[assignment]

        # Handle same-type mapping with service ID
        if mapped_item.service_id:
            context.log.info(
                f"Using mapping for {item.artist} - {item.title} "
                f"-> ID {mapped_item.service_id}"
            )
            return mapped_item

        # Mapping has metadata but no ID - search for it
        context.log.info(
            f"Using mapping for {item.artist} - {item.title} "
            f"-> {mapped_item.artist} - {mapped_item.title}"
        )
        search_results = context.operations.search(mapped_item)
        if search_results:
            best_match, _ = get_best_match(
                source=mapped_item,
                candidates=search_results,
                min_similarity=context.min_similarity,
            )
            return cast(T, best_match)

        return None

    def _get_service_client(self, context: MatchContext[T]):
        """Get service client for ID type detection"""
        if context.service.service_name == "spotify" and hasattr(context.service, "sp"):
            return context.service.sp
        return None


class SearchMatchStrategy(MatchStrategy[T]):
    """Try to match by searching the service"""

    def _try_match(self, context: MatchContext[T]) -> T | None:
        search_results = context.operations.search(context.item)
        if not search_results:
            return None

        best_match, _ = get_best_match(
            source=context.item,
            candidates=search_results,
            min_similarity=context.min_similarity,
        )
        return cast(T, best_match)


# ============================================================================
# Cross-Type Mapping Handler
# ============================================================================


class CrossTypeMappingHandler(Generic[T]):
    """Handles the complex logic of cross-type mappings (album->track, track->album)"""

    def __init__(self, service: MusicService, log: Any):
        self.service = service
        self.log = log

    def handle_album_to_track(self, album: Album, track: Track) -> PushResult[Album]:
        """Handle mapping an album to a track"""
        self.log.info(
            f"Cross-type mapping: album {album.artist} - {album.title} mapped to track"
        )

        try:
            if self.service.is_track_in_library(track):
                return PushResult(
                    item=album,
                    found_item=None,
                    status=PushStatus.already_in_library,
                    message="Mapped track already in library",
                )

            success = self.service.add_track(track)
            if success:
                return PushResult(
                    item=album,
                    found_item=None,
                    status=PushStatus.added,
                    message="Added as track (album→track mapping)",
                )
            else:
                return PushResult(item=album, status=PushStatus.error)

        except Exception as e:
            self.log.error(f"Error adding mapped track: {e}")
            return PushResult(item=album, status=PushStatus.error)

    def handle_track_to_album(self, track: Track, album: Album) -> PushResult[Track]:
        """Handle mapping a track to an album"""
        self.log.info(
            f"Cross-type mapping: track {track.artist} - {track.title} mapped to album"
        )

        try:
            if self.service.is_album_in_library(album):
                return PushResult(
                    item=track,
                    found_item=None,
                    status=PushStatus.already_in_library,
                    message="Mapped album already in library",
                )

            success = self.service.add_album(album)
            if success:
                return PushResult(
                    item=track,
                    found_item=None,
                    status=PushStatus.added,
                    message="Added as album (track→album mapping)",
                )
            else:
                return PushResult(item=track, status=PushStatus.error)

        except Exception as e:
            self.log.error(f"Error adding mapped album: {e}")
            return PushResult(item=track, status=PushStatus.error)


# ============================================================================
# Item Processor - Handles the push logic for a single item
# ============================================================================


class ItemProcessor(Generic[T]):
    """Processes a single item through the push pipeline"""

    def __init__(
        self,
        operations: ItemOperations[T],
        match_chain: MatchStrategy[T],
        filter: AlbumFilter | TrackFilter | None,
        mappings: MappingsManager | None,
        min_similarity: float,
    ):
        self.operations = operations
        self.match_chain = match_chain
        self.filter = filter
        self.mappings = mappings
        self.min_similarity = min_similarity
        self.log = get_logger()
        self.cross_type_handler = CrossTypeMappingHandler(operations.service, self.log)

    def process(self, item: T) -> PushResult[T]:
        """Process a single item through the push pipeline"""

        # Step 1: Check filter
        if self._should_filter(item):
            return PushResult(item=item, status=PushStatus.filtered)  # type: ignore[arg-type]

        # Step 2: Check if already in library
        try:
            if self.operations.is_in_library(item):
                return PushResult(item=item, status=PushStatus.already_in_library)  # type: ignore[arg-type]
        except Exception as e:
            self.log.error(f"Failed to check library: {e}")
            raise

        # Step 3: Check for cross-type mapping
        cross_type_result = self._check_cross_type_mapping(item)
        if cross_type_result:
            return cross_type_result

        # Step 4: Find a match using the chain of strategies
        context = MatchContext(
            item=item,  # type: ignore[arg-type]
            operations=self.operations,
            service=self.operations.service,
            mappings=self.mappings,
            min_similarity=self.min_similarity,
            log=self.log,
        )

        best_match = self.match_chain.find_match(context)

        if not best_match:
            return PushResult(item=item, status=PushStatus.not_found)  # type: ignore[arg-type]

        # Step 5: Double-check if match is in library and add if not
        return self._add_match(item, best_match)

    def _should_filter(self, item: T) -> bool:
        """Check if item should be filtered out"""
        if not self.filter:
            return False
        return self.filter.should_filter_out(item)  # type: ignore[arg-type]

    def _check_cross_type_mapping(self, item: T) -> PushResult[T] | None:
        """Check for cross-type mappings and handle them"""
        if not self.mappings:
            return None

        service_client = None
        if self.operations.service.service_name == "spotify" and hasattr(
            self.operations.service, "sp"
        ):
            service_client = self.operations.service.sp

        # Check for cross-type mapping
        # Type checker can't narrow T based on isinstance, but runtime logic is correct
        if isinstance(item, Album):
            mapped = self.mappings.get_album_mapping(
                item, self.operations.service.service_name, service_client
            )
            if mapped and isinstance(mapped, Track):
                # We know item is Album here, but T could be Album or Track
                # Safe to cast since we're returning PushResult[T] where T=Album
                result = self.cross_type_handler.handle_album_to_track(item, mapped)
                return result  # type: ignore[return-value]

        elif isinstance(item, Track):
            mapped = self.mappings.get_track_mapping(
                item, self.operations.service.service_name, service_client
            )
            if mapped and isinstance(mapped, Album):
                # We know item is Track here, but T could be Album or Track
                # Safe to cast since we're returning PushResult[T] where T=Track
                result = self.cross_type_handler.handle_track_to_album(item, mapped)
                return result  # type: ignore[return-value]

        return None

    def _add_match(self, item: T, match: T) -> PushResult[T]:
        """Add the matched item to library"""
        try:
            # Double-check if already in library
            if self.operations.is_in_library(match):
                return PushResult(  # type: ignore[arg-type]
                    item=item,  # type: ignore[arg-type]
                    found_item=match,  # type: ignore[arg-type]
                    status=PushStatus.already_in_library,
                )

            # Add to library
            success = self.operations.add(match)
            if success:
                return PushResult(  # type: ignore[arg-type]
                    item=item,  # type: ignore[arg-type]
                    found_item=match,  # type: ignore[arg-type]
                    status=PushStatus.added,
                )
            else:
                return PushResult(  # type: ignore[arg-type]
                    item=item,  # type: ignore[arg-type]
                    found_item=match,  # type: ignore[arg-type]
                    status=PushStatus.error,
                )
        except Exception as e:
            self.log.error(f"Failed to add item: {e}")
            raise


# ============================================================================
# Main Pusher Classes
# ============================================================================


class AlbumPusher:
    """Pushes albums to a music service"""

    def __init__(
        self,
        items: list[Album],
        service: MusicService,
        filter: AlbumFilter | None = None,
        min_similarity: float = 0.8,
        mappings: MappingsManager | None = None,
    ):
        self.items = items
        self.service = service
        self.operations = AlbumOperations(service)
        self.filter = filter
        self.min_similarity = min_similarity
        self.mappings = mappings

    def push(self) -> list[PushResult[Album]]:
        """Push albums to the service"""
        log = get_logger()
        log.info(f"Got {len(self.items)} albums to push")

        # Build the chain of responsibility for matching
        match_chain: MatchStrategy[Album] = ServiceIdMatchStrategy[Album](
            MappingMatchStrategy[Album](SearchMatchStrategy[Album]())
        )

        # Create processor
        processor: ItemProcessor[Album] = ItemProcessor(
            operations=self.operations,
            match_chain=match_chain,
            filter=self.filter,
            mappings=self.mappings,
            min_similarity=self.min_similarity,
        )

        # Process each item
        results: list[PushResult[Album]] = []
        for item in self.items:
            try:
                result = processor.process(item)
                self._add_result(results, result)
            except Exception as e:
                log.error(f"Fatal error processing album: {e}")
                raise

        return results

    def _add_result(
        self, results: list[PushResult[Album]], result: PushResult[Album]
    ) -> None:
        """Add a result and log it"""
        log = get_logger()
        results.append(result)
        message = pretty_print_result(result)

        if result.status == PushStatus.error:
            log.error(message)
        else:
            log.info(message)


class TrackPusher:
    """Pushes tracks to a music service"""

    def __init__(
        self,
        items: list[Track],
        service: MusicService,
        filter: TrackFilter | None = None,
        min_similarity: float = 0.8,
        mappings: MappingsManager | None = None,
    ):
        self.items = items
        self.service = service
        self.operations = TrackOperations(service)
        self.filter = filter
        self.min_similarity = min_similarity
        self.mappings = mappings

    def push(self) -> list[PushResult[Track]]:
        """Push tracks to the service"""
        log = get_logger()
        log.info(f"Got {len(self.items)} tracks to push")

        # Build the chain of responsibility for matching
        match_chain: MatchStrategy[Track] = ServiceIdMatchStrategy[Track](
            MappingMatchStrategy[Track](SearchMatchStrategy[Track]())
        )

        # Create processor
        processor: ItemProcessor[Track] = ItemProcessor(
            operations=self.operations,
            match_chain=match_chain,
            filter=self.filter,
            mappings=self.mappings,
            min_similarity=self.min_similarity,
        )

        # Process each item
        results: list[PushResult[Track]] = []
        for item in self.items:
            try:
                result = processor.process(item)
                self._add_result(results, result)
            except Exception as e:
                log.error(f"Fatal error processing track: {e}")
                raise

        return results

    def _add_result(
        self, results: list[PushResult[Track]], result: PushResult[Track]
    ) -> None:
        """Add a result and log it"""
        log = get_logger()
        results.append(result)
        message = pretty_print_result(result)

        if result.status == PushStatus.error:
            log.error(message)
        else:
            log.info(message)


# ============================================================================
# Utility Functions
# ============================================================================


def pretty_print_result(result: PushResult) -> str:
    """Format a push result for display."""
    item = result.item
    match result.status:
        case PushStatus.error:
            return f"Failed to add {item.artist} - {item.title}"
        case PushStatus.not_found:
            return f"Could not find a match for {item.artist} - {item.title}"
        case PushStatus.already_in_library:
            msg = f"Skipping {item.artist} - {item.title} (already in library)"
            if result.message:
                msg += f" - {result.message}"
            return msg
        case PushStatus.filtered:
            return f"Skipping {item.artist} - {item.title} (filtered)"
        case PushStatus.similarity_too_low:
            return f"Skipping {item.artist} - {item.title} (similarity too low)"
        case PushStatus.mapped:
            if result.found_item:
                return f"Added {item.artist} - {item.title} -> Mapped to {result.found_item.artist} - {result.found_item.title}"
            return f"Added {item.artist} - {item.title} (mapped)"
        case PushStatus.added:
            if result.message:
                return f"Added {item.artist} - {item.title} -> {result.message}"
            elif result.found_item:
                return f"Added {item.artist} - {item.title} -> Found {result.found_item.artist} - {result.found_item.title}"
            else:
                return f"Added {item.artist} - {item.title}"
        case PushStatus.deleted:
            return f"Deleted {item.artist} - {item.title} from target library"
        case _:
            return (
                f"Something unknown happened while adding {item.artist} - {item.title}"
            )
