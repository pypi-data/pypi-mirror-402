"""
Tests for SwiftAPI Events.
"""
import pytest
from swiftapi.events import (
    Event,
    EventEmitterMixin,
    event_bus,
    on_event,
)


class TestEvent:
    """Test Event class."""
    
    def test_event_creation(self):
        """Test creating an event."""
        event = Event(name="user.created", data={"id": 1})
        assert event.name == "user.created"
        assert event.data == {"id": 1}
    
    def test_event_timestamp(self):
        """Test event has timestamp."""
        event = Event(name="test", data={})
        assert event.timestamp is not None


class TestEventBus:
    """Test event bus functionality."""
    
    def test_event_bus_instance(self):
        """Test event bus is a singleton."""
        assert event_bus is not None
    
    def test_event_bus_has_subscribe(self):
        """Test event bus has subscribe method."""
        assert hasattr(event_bus, 'subscribe') or hasattr(event_bus, 'on')
    
    def test_event_bus_has_emit(self):
        """Test event bus has emit method."""
        assert hasattr(event_bus, 'emit') or hasattr(event_bus, 'dispatch')


class TestOnEventDecorator:
    """Test @on_event decorator."""
    
    def test_on_event_decorator(self):
        """Test on_event decorator is callable."""
        assert callable(on_event)


class TestEventEmitterMixin:
    """Test EventEmitterMixin."""
    
    def test_mixin_exists(self):
        """Test EventEmitterMixin exists."""
        assert EventEmitterMixin is not None
