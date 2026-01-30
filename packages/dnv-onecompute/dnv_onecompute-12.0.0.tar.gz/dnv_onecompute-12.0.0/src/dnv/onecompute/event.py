"""Module for the Event class, providing an asynchronous event handling system."""

import asyncio


class Event:
    """Event handling class for asynchronous operations."""

    def __init__(self):
        """Initialize an Event with an empty set of handlers."""
        self.handlers = set()

    def handle(self, handler):
        """Add a handler to the set of handlers for this event."""
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        """Remove a handler from the set of handlers for this event."""
        try:
            self.handlers.remove(handler)
        except Exception as ex:
            raise ValueError(
                "Handler is not handling this event, so cannot unhandle it."
            ) from ex
        return self

    async def fire_async(self, *args, **kwargs):
        """Asynchronously call all handlers with the given arguments."""
        handlers = [
            asyncio.ensure_future(handler(*args, **kwargs)) for handler in self.handlers
        ]
        await asyncio.gather(*handlers)

    @property
    def handler_count(self):
        """Return the number of handlers for this event."""
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire_async
    __len__ = handler_count
