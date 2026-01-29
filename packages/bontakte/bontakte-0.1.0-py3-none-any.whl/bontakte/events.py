from dataclasses import dataclass
from typing import Any, Dict, Optional
from .types import Message, User


@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    
    @classmethod
    def from_vk_update(cls, update: Dict[str, Any]) -> 'Event':
        event_type = update.get("type", "unknown")
        return cls(type=event_type, data=update)


@dataclass
class MessageEvent(Event):
    message: Message
    user: Optional[User] = None
    
    @classmethod
    def from_vk_update(cls, update: Dict[str, Any]) -> 'MessageEvent':
        from .utils import parse_message, parse_user
        
        message_data = update.get("object", {}).get("message", {})
        message = parse_message(message_data)
        
        user_data = message_data.get("from_id")
        user = parse_user({"id": user_data}) if user_data else None
        
        return cls(
            type="message_new",
            data=update,
            message=message,
            user=user
        )
