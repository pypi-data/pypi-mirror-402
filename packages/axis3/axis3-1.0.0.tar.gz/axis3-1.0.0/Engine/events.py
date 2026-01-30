"""
Event system for decoupled communication between systems.
"""
from typing import Dict, List, Callable, Any, Optional
from enum import Enum


class EventType(Enum):
    """Built-in event types."""
    # Window events
    WINDOW_CLOSE = "window_close"
    WINDOW_RESIZE = "window_resize"
    WINDOW_FOCUS = "window_focus"
    WINDOW_LOST_FOCUS = "window_lost_focus"
    
    # Input events
    KEY_PRESSED = "key_pressed"
    KEY_RELEASED = "key_released"
    MOUSE_MOVED = "mouse_moved"
    MOUSE_BUTTON_PRESSED = "mouse_button_pressed"
    MOUSE_BUTTON_RELEASED = "mouse_button_released"
    MOUSE_SCROLLED = "mouse_scrolled"
    
    # Scene events
    SCENE_LOADED = "scene_loaded"
    SCENE_UNLOADED = "scene_unloaded"
    
    # Game events
    ENTITY_CREATED = "entity_created"
    ENTITY_DESTROYED = "entity_destroyed"
    COMPONENT_ADDED = "component_added"
    COMPONENT_REMOVED = "component_removed"


class Event:
    """Base event class."""
    
    def __init__(self, event_type: EventType, data: Any = None, consumed: bool = False):
        """
        Initialize event.
        
        Args:
            event_type: Type of event
            data: Event data
            consumed: Whether event has been consumed (stops propagation)
        """
        self.type = event_type
        self.data = data
        self.consumed = consumed
    
    def consume(self):
        """Mark event as consumed."""
        self.consumed = True
    
    def __repr__(self):
        return f"Event(type={self.type}, data={self.data}, consumed={self.consumed})"


class EventDispatcher:
    """Event dispatcher for managing event subscriptions and dispatching."""
    
    def __init__(self):
        """Initialize event dispatcher."""
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_queue: List[Event] = []
        self._processing = False
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to listen for
            callback: Callback function (takes Event as parameter)
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from an event type."""
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
    
    def dispatch(self, event: Event):
        """
        Dispatch an event immediately.
        
        Args:
            event: Event to dispatch
        """
        if self._processing:
            # Queue event if we're currently processing events
            self._event_queue.append(event)
            return
        
        self._process_event(event)
    
    def dispatch_later(self, event: Event):
        """Queue an event to be dispatched later."""
        self._event_queue.append(event)
    
    def dispatch_immediate(self, event_type: EventType, data: Any = None):
        """Create and dispatch an event immediately."""
        event = Event(event_type, data)
        self.dispatch(event)
    
    def _process_event(self, event: Event):
        """Process a single event."""
        if event.type in self._listeners:
            for callback in self._listeners[event.type]:
                if event.consumed:
                    break
                callback(event)
    
    def process_queue(self):
        """Process all queued events."""
        self._processing = True
        while self._event_queue:
            event = self._event_queue.pop(0)
            self._process_event(event)
        self._processing = False
    
    def clear_queue(self):
        """Clear event queue."""
        self._event_queue.clear()
    
    def clear_listeners(self, event_type: Optional[EventType] = None):
        """Clear listeners for an event type, or all if None."""
        if event_type is None:
            self._listeners.clear()
        elif event_type in self._listeners:
            self._listeners[event_type].clear()
    
    def has_listeners(self, event_type: EventType) -> bool:
        """Check if event type has any listeners."""
        return event_type in self._listeners and len(self._listeners[event_type]) > 0


# Global event dispatcher instance
_event_dispatcher: Optional[EventDispatcher] = None


def get_event_dispatcher() -> EventDispatcher:
    """Get global event dispatcher instance."""
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = EventDispatcher()
    return _event_dispatcher

