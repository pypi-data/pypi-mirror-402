from typing import TYPE_CHECKING, Dict, Any
from .author import Author
if TYPE_CHECKING:
    from ..ws.socket import WebSocketClient
class Reaction:
    def __init__(self, ws: 'WebSocketClient', data: Dict[str, Any]):
        self.ws = ws
        self.data = data
        self.message_id = data.get("message_id")
        self.channel_id = data.get("channel_id")
        self.emoji = data.get("emoji")
        user_data = data.get("user", {})
        user_data["user_id"] = user_data.get("id")
        self.author = Author(user_data)
    
    async def add(self, emoji: str) -> None:
        if self.message_id:
            await self.ws.react(self.message_id, emoji)
    
    async def remove(self, emoji: str) -> None:
        if self.message_id:
            await self.ws.unreact(self.message_id, emoji)
