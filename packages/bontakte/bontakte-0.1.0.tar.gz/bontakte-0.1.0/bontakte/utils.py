from typing import Dict, Any, Optional, List
from datetime import datetime
from .types import Message, User, Attachment


def parse_message(data: Dict[str, Any]) -> Message:
    attachments = []
    if "attachments" in data:
        for att_data in data["attachments"]:
            attachments.append(Attachment(
                type=att_data.get("type", ""),
                url=att_data.get("url"),
                data=att_data
            ))
    
    forward_messages = []
    if "fwd_messages" in data:
        for fwd_data in data["fwd_messages"]:
            forward_messages.append(parse_message(fwd_data))
    
    return Message(
        id=data.get("id", 0),
        text=data.get("text", ""),
        user_id=data.get("from_id", 0),
        chat_id=data.get("peer_id", 0),
        date=datetime.fromtimestamp(data.get("date", 0)),
        attachments=attachments,
        reply_to=data.get("reply_to"),
        forward_messages=forward_messages
    )


def parse_user(data: Dict[str, Any]) -> User:
    return User(
        id=data.get("id", 0),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        username=data.get("screen_name"),
        photo=data.get("photo_100"),
        is_bot=False
    )


def parse_chat(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": data.get("peer", {}).get("id", 0),
        "type": data.get("peer", {}).get("type", "user"),
        "title": data.get("chat_settings", {}).get("title"),
        "members_count": data.get("chat_settings", {}).get("members_count")
    }
