import requests
from typing import Dict, Any, Optional, List
import time


class VKAPI:
    def __init__(self, access_token: str, api_version: str = "5.131"):
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = "https://api.vk.com/method"
        self.session = requests.Session()
    
    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params.update({
            "access_token": self.access_token,
            "v": self.api_version
        })
        
        response = self.session.post(
            f"{self.base_url}/{method}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise Exception(f"VK API Error: {data['error'].get('error_msg', 'Unknown error')}")
        
        return data.get("response", {})
    
    def messages_send(self, peer_id: int, message: str, **kwargs) -> int:
        params = {
            "peer_id": peer_id,
            "message": message,
            "random_id": int(time.time() * 1000),
            **kwargs
        }
        result = self._make_request("messages.send", params)
        return result.get("peer_id", 0)
    
    def messages_get_conversations(self, offset: int = 0, count: int = 20, **kwargs) -> Dict[str, Any]:
        params = {
            "offset": offset,
            "count": count,
            **kwargs
        }
        return self._make_request("messages.getConversations", params)
    
    def messages_get_history(self, peer_id: int, offset: int = 0, count: int = 20, **kwargs) -> Dict[str, Any]:
        params = {
            "peer_id": peer_id,
            "offset": offset,
            "count": count,
            **kwargs
        }
        return self._make_request("messages.getHistory", params)
    
    def users_get(self, user_ids: List[int], **kwargs) -> List[Dict[str, Any]]:
        params = {
            "user_ids": ",".join(map(str, user_ids)),
            **kwargs
        }
        return self._make_request("users.get", params)
    
    def groups_get_long_poll_server(self, group_id: int) -> Dict[str, Any]:
        params = {"group_id": group_id}
        return self._make_request("groups.getLongPollServer", params)
