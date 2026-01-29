import asyncio
import requests
from typing import List, Optional, Callable, Any, Dict
from .api import VKAPI
from .events import Event, MessageEvent
from .handlers import Handler, MessageHandler
from .utils import parse_message, parse_user


class Bot:
    """
    Основной класс для работы с ботом ВКонтакте.
    Разработан Triazov Kirill (triazov.ru)
    """
    def __init__(self, access_token: str, group_id: int = None, api_version: str = "5.131"):
        self.api = VKAPI(access_token, api_version)
        self.group_id = group_id
        self.handlers: List[Handler] = []
        self.running = False
        self.long_poll_server = None
        self.long_poll_key = None
        self.long_poll_ts = None
    
    def message_handler(self, filters: Optional[Callable] = None):
        def decorator(callback: Callable):
            handler = MessageHandler(callback, filters)
            self.handlers.append(handler)
            return callback
        return decorator
    
    def event_handler(self, event_type: str):
        def decorator(callback: Callable):
            handler = Handler(callback, event_type)
            self.handlers.append(handler)
            return callback
        return decorator
    
    def add_handler(self, handler: Handler):
        self.handlers.append(handler)
    
    async def send_message(self, peer_id: int, text: str, **kwargs) -> int:
        return self.api.messages_send(peer_id, text, **kwargs)
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        users = self.api.users_get([user_id])
        return users[0] if users else None
    
    def _init_long_poll(self):
        if not self.group_id:
            raise ValueError("group_id is required for long poll")
        
        server_data = self.api.groups_get_long_poll_server(self.group_id)
        self.long_poll_server = server_data.get("server")
        self.long_poll_key = server_data.get("key")
        self.long_poll_ts = server_data.get("ts")
    
    def _get_updates(self) -> List[Dict[str, Any]]:
        if not self.long_poll_server:
            self._init_long_poll()
        
        url = f"{self.long_poll_server}?act=a_check&key={self.long_poll_key}&ts={self.long_poll_ts}&wait=25"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("failed"):
                if data["failed"] == 1:
                    self.long_poll_ts = data.get("ts")
                elif data["failed"] in [2, 3]:
                    self._init_long_poll()
                return []
            
            self.long_poll_ts = data.get("ts")
            return data.get("updates", [])
        except Exception as e:
            print(f"Error getting updates: {e}")
            return []
    
    async def _process_update(self, update: Dict[str, Any]):
        event_type = update.get("type")
        
        if event_type == "message_new":
            try:
                event = MessageEvent.from_vk_update(update)
                if event.user is None and event.message.user_id:
                    user_data = await self.get_user(event.message.user_id)
                    if user_data:
                        event.user = parse_user(user_data)
            except Exception as e:
                print(f"Error parsing message event: {e}")
                event = Event.from_vk_update(update)
        else:
            event = Event.from_vk_update(update)
        
        for handler in self.handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                print(f"Error in handler: {e}")
    
    async def _poll_loop(self):
        while self.running:
            updates = self._get_updates()
            for update in updates:
                await self._process_update(update)
            await asyncio.sleep(0.1)
    
    async def start_polling(self):
        if self.running:
            return
        
        self.running = True
        if self.group_id:
            self._init_long_poll()
        
        await self._poll_loop()
    
    def run(self):
        asyncio.run(self.start_polling())
    
    def stop(self):
        self.running = False
