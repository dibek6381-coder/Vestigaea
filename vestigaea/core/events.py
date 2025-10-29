"""Simple event bus utilities used across the project."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, Iterable, List


class EventBus:
    """A minimal publish/subscribe bus with defensive safeguards."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Register *callback* to be invoked when *event_type* is published.

        Duplicate registrations are ignored so systems can freely subscribe in
        constructors without worrying about multiple initialisations (which
        happens during game restarts in the MVP).
        """

        listeners = self._subscribers[event_type]
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Remove *callback* from the listeners of *event_type* if present."""

        listeners = self._subscribers.get(event_type)
        if not listeners:
            return

        try:
            listeners.remove(callback)
        except ValueError:
            return

        if not listeners:
            del self._subscribers[event_type]

    def publish(self, event_type: str, data: Any | None = None) -> None:
        """Emit *event_type* to all listeners.

        A snapshot of the subscribers is iterated to ensure callbacks can
        safely subscribe/unsubscribe during handling without affecting the
        current dispatch.
        """

        for callback in list(self._subscribers.get(event_type, [])):
            callback(data)

    def clear(self, event_type: str | None = None) -> None:
        """Remove all listeners.

        When *event_type* is ``None`` the entire bus is cleared; otherwise only
        the listeners for the specific event are removed.  This is helpful when
        resetting global state between tests.
        """

        if event_type is None:
            self._subscribers.clear()
        else:
            self._subscribers.pop(event_type, None)

    def iter_subscribers(self, event_type: str) -> Iterable[Callable[[Any], None]]:
        """Expose an immutable snapshot of listeners (primarily for testing)."""

        return tuple(self._subscribers.get(event_type, ()))


# Global event bus instance
bus = EventBus()

