"""
Bontakte - Python-библиотека для создания ботов ВКонтакте
Разработано Triazov Kirill (https://triazov.ru)
"""

from .client import Bot
from .types import Message, User, Chat, Attachment
from .events import Event, MessageEvent
from .handlers import Handler, MessageHandler

__version__ = "0.1.0"
__author__ = "Triazov Kirill"
__author_email__ = "info@triazov.ru"
__website__ = "https://triazov.ru"
__all__ = [
    "Bot",
    "Message",
    "User",
    "Chat",
    "Attachment",
    "Event",
    "MessageEvent",
    "Handler",
    "MessageHandler",
]
