from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    username: Optional[str] = None
    photo: Optional[str] = None
    is_bot: bool = False
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Attachment:
    type: str
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    members_count: Optional[int] = None


@dataclass
class Message:
    id: int
    text: str
    user_id: int
    chat_id: int
    date: datetime
    attachments: List[Attachment] = None
    reply_to: Optional[int] = None
    forward_messages: List['Message'] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.forward_messages is None:
            self.forward_messages = []
