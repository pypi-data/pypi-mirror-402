"""
Subscriber for Rhizo changelog events.

Provides both polling-based iteration and callback interfaces
for processing changelog entries as they become available.

This enables the unified batch/stream model:
- Batch: "What is the state?" -> engine.query()
- Stream: "What changed?" -> engine.subscribe() or engine.get_changes()
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, List, Callable, Iterator
import time
import threading

from .logging import get_logger

_logger = get_logger(__name__)

if TYPE_CHECKING:
    import _rhizo


@dataclass
class ChangeEvent:
    """
    A single table change event for subscriber consumption.

    Each ChangeEvent represents one table changing within a transaction.
    A transaction that modifies multiple tables produces multiple ChangeEvents.

    Attributes:
        tx_id: Transaction ID that made this change
        committed_at: Unix timestamp when the transaction was committed
        branch: Branch the change was made on
        table_name: Name of the table that changed
        old_version: Previous version (None if new table)
        new_version: New version after this change
        chunk_hashes: List of chunk hashes for the new version
    """
    tx_id: int
    committed_at: int
    branch: str
    table_name: str
    old_version: Optional[int]
    new_version: int
    chunk_hashes: List[str]

    @classmethod
    def from_changelog_entry(cls, entry: "_rhizo.PyChangelogEntry") -> List["ChangeEvent"]:
        """
        Convert a changelog entry to individual change events.

        Args:
            entry: A PyChangelogEntry from the Rust bindings

        Returns:
            List of ChangeEvent objects, one per table changed
        """
        events = []
        for change in entry.changes:
            events.append(cls(
                tx_id=entry.tx_id,
                committed_at=entry.committed_at,
                branch=entry.branch,
                table_name=change.table_name,
                old_version=change.old_version,
                new_version=change.new_version,
                chunk_hashes=change.chunk_hashes,
            ))
        return events

    def is_new_table(self) -> bool:
        """Check if this change created a new table."""
        return self.old_version is None


class Subscriber:
    """
    Subscribes to changelog events from UDR.

    Supports both polling-based iteration and callback interfaces.
    This is the streaming half of the unified batch/stream model.

    Example (iterator - blocking):
        >>> subscriber = Subscriber(tx_manager, since_tx_id=100)
        >>> for event in subscriber:
        ...     print(f"{event.table_name}: v{event.old_version} -> v{event.new_version}")
        ...     if some_condition:
        ...         break  # Exit when done

    Example (poll - non-blocking):
        >>> subscriber = Subscriber(tx_manager)
        >>> events = subscriber.poll()  # Returns immediately
        >>> for event in events:
        ...     process(event)

    Example (callback - blocking):
        >>> def on_change(event):
        ...     print(f"Change: {event.table_name}")
        >>> subscriber = Subscriber(tx_manager)
        >>> subscriber.subscribe(on_change)  # Blocks forever

    Example (background thread):
        >>> subscriber = Subscriber(tx_manager)
        >>> subscriber.start_background(on_change)  # Non-blocking
        >>> # ... do other work ...
        >>> subscriber.stop()  # Stop background processing
    """

    def __init__(
        self,
        transaction_manager: "_rhizo.PyTransactionManager",
        since_tx_id: Optional[int] = None,
        tables: Optional[List[str]] = None,
        branch: Optional[str] = None,
        poll_interval: float = 1.0,
    ):
        """
        Create a new subscriber.

        Args:
            transaction_manager: The transaction manager to subscribe to
            since_tx_id: Start from this transaction (exclusive).
                        None = start from current latest (won't see past events)
            tables: Only receive events for these tables. None = all tables
            branch: Only receive events for this branch. None = all branches
            poll_interval: Seconds between polls when waiting for new events (default: 1.0)
        """
        self._tx_manager = transaction_manager
        self._tables = tables
        self._branch = branch
        self._poll_interval = poll_interval

        # Initialize cursor
        if since_tx_id is not None:
            self._last_tx_id = since_tx_id
        else:
            # Start from current latest (don't replay history)
            latest = self._tx_manager.latest_tx_id()
            self._last_tx_id = latest if latest is not None else 0

        # Background thread state
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def __iter__(self) -> Iterator[ChangeEvent]:
        """
        Iterate over changelog events (polling, blocking).

        This is an infinite iterator that polls for new events.
        Use break to exit, or use poll() for non-blocking access.

        Yields:
            ChangeEvent for each table change
        """
        while True:
            entries = self._poll()

            if entries:
                for entry in entries:
                    for event in ChangeEvent.from_changelog_entry(entry):
                        yield event
            else:
                # No new events, wait before next poll
                time.sleep(self._poll_interval)

    def poll(self) -> List[ChangeEvent]:
        """
        Poll for new events without blocking.

        Returns events since last poll. Returns empty list if no new events.
        Updates the internal cursor so next poll returns only newer events.

        Returns:
            List of ChangeEvent objects (empty if no new events)
        """
        entries = self._poll()
        events = []
        for entry in entries:
            events.extend(ChangeEvent.from_changelog_entry(entry))
        return events

    def subscribe(self, callback: Callable[[ChangeEvent], None]) -> None:
        """
        Subscribe with a callback (blocking).

        Calls the callback for each new event. Blocks forever
        (or until interrupted with Ctrl+C).

        Args:
            callback: Function to call for each event
        """
        for event in self:
            callback(event)

    def start_background(self, callback: Callable[[ChangeEvent], None]) -> None:
        """
        Start a background thread to process events.

        The callback is called for each new event in a daemon thread.
        Use stop() to terminate the background processing.

        Args:
            callback: Function to call for each event

        Raises:
            RuntimeError: If subscriber is already running
        """
        if self._running:
            raise RuntimeError("Subscriber already running")

        self._running = True
        self._thread = threading.Thread(
            target=self._background_loop,
            args=(callback,),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the background subscriber.

        Waits for the background thread to finish (up to 2x poll_interval).
        Safe to call even if not running.
        """
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._poll_interval * 2)
            self._thread = None

    @property
    def last_tx_id(self) -> int:
        """Get the last processed transaction ID (cursor position)."""
        return self._last_tx_id

    @property
    def is_running(self) -> bool:
        """Check if background subscriber is running."""
        return self._running

    def _poll(self) -> List["_rhizo.PyChangelogEntry"]:
        """
        Poll for new changelog entries from the transaction manager.

        Updates the internal cursor (_last_tx_id) if new entries are found.
        """
        entries = self._tx_manager.get_changelog(
            since_tx_id=self._last_tx_id,
            tables=self._tables,
            branch=self._branch,
        )

        if entries:
            self._last_tx_id = entries[-1].tx_id

        return entries

    def _background_loop(self, callback: Callable[[ChangeEvent], None]) -> None:
        """Background thread main loop."""
        while self._running:
            try:
                entries = self._poll()
                for entry in entries:
                    for event in ChangeEvent.from_changelog_entry(entry):
                        if not self._running:
                            return
                        callback(event)

                if not entries:
                    time.sleep(self._poll_interval)
            except Exception as e:
                # Log error but continue processing
                _logger.warning("Subscriber error: %s", e)
                time.sleep(self._poll_interval)
