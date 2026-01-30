from typing import TYPE_CHECKING, Optional, Dict, Any
from .author import Author

if TYPE_CHECKING:
    from ..ws.socket import WebSocketClient


class Interaction:
    def __init__(self, ws: 'WebSocketClient', data: Dict[str, Any]):
        self.ws = ws
        self.data = data
        self.custom_id = data.get("customId")
        self.channel_id = data.get("channelId")
        self.message_id = data.get("messageId")
        self.interaction_id = data.get("id")
        user_data = data.get("user", {})
        user_data["user_id"] = user_data.get("id")
        self.author = Author(user_data)
    
    async def send(self, content: str, ephemeral: bool = False) -> None:
        if ephemeral:
            await self.ws.reply_interaction(self.interaction_id, content, ephemeral)
        else:
            await self.ws.send_message(self.channel_id, content)
    
    async def reply(self, content: str, ephemeral: bool = False) -> None:
        if ephemeral:
            await self.ws.reply_interaction(self.interaction_id, content, ephemeral)
        else:
            await self.ws.send_message(self.channel_id, content, reply_to=self.message_id)
    
    async def delete(self) -> None:
        if self.message_id:
            await self.ws.delete_message(self.message_id)
