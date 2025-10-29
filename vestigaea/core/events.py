"""
Simple event bus for Vestigaea MVP.
Allows systems to communicate via events without direct coupling.
"""
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    """Simple publish/subscribe event system."""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)
    
    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Register a callback to be called when an event occurs."""
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Remove a callback from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
    
    def publish(self, event_type: str, data: Any = None) -> None:
        """Emit an event to all subscribers."""
        for callback in self._subscribers.get(event_type, []):
            callback(data)

# Global event bus instance
bus = EventBus()