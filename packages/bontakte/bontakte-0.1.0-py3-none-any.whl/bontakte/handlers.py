from typing import Callable, Any, Optional
from .events import Event, MessageEvent


class Handler:
    def __init__(self, callback: Callable, event_type: str = None):
        self.callback = callback
        self.event_type = event_type
    
    def check(self, event: Event) -> bool:
        if self.event_type:
            return event.type == self.event_type
        return True
    
    async def handle(self, event: Event) -> Any:
        if self.check(event):
            if callable(self.callback):
                return await self.callback(event)
        return None


class MessageHandler(Handler):
    def __init__(self, callback: Callable, filters: Optional[Callable] = None):
        super().__init__(callback, event_type="message_new")
        self.filters = filters
    
    def check(self, event: Event) -> bool:
        if not isinstance(event, MessageEvent):
            return False
        
        if self.filters:
            return self.filters(event)
        
        return True
    
    async def handle(self, event: Event) -> Any:
        if isinstance(event, MessageEvent) and self.check(event):
            if callable(self.callback):
                return await self.callback(event)
        return None
