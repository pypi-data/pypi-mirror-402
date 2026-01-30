from typing import TYPE_CHECKING, Optional, Dict, Any, List, Union
from .author import Author

if TYPE_CHECKING:
    from ..ws.socket import WebSocketClient
    from ..embeds import Embed
    from ..utils.components import ActionRow


class Context:
    def __init__(self, ws: 'WebSocketClient', data: Dict[str, Any]):
        self.ws = ws
        self.data = data
        self.message_id = data.get("id")
        self.channel_id = data.get("channel_id")
        self.server_id = data.get("server_id")
        self.user_id = data.get("user_id")
        self.content = data.get("content", "")
        self.author = Author(data)
    
    async def send(self, content: Optional[str] = None, embed: Optional['Embed'] = None, embeds: Optional[List['Embed']] = None, components: Optional[List['ActionRow']] = None) -> None:
        embed_list = None
        if embed:
            embed_list = [embed.to_dict()]
        elif embeds:
            embed_list = [e.to_dict() for e in embeds[:10]]
        
        component_list = None
        if components:
            component_list = [c.to_dict() for c in components[:5]]
        
        await self.ws.send_message(self.channel_id, content, embed_list, component_list)
    
    async def reply(self, content: Optional[str] = None, embed: Optional['Embed'] = None, embeds: Optional[List['Embed']] = None, components: Optional[List['ActionRow']] = None) -> None:
        await self.send(content, embed, embeds, components)
    
    async def edit(self, content: str) -> None:
        if self.message_id:
            await self.ws.edit_message(self.message_id, content)
    
    async def delete(self) -> None:
        if self.message_id:
            await self.ws.delete_message(self.message_id)
    
    async def react(self, emoji: str) -> None:
        if self.message_id:
            await self.ws.react(self.message_id, emoji)
    
    async def unreact(self, emoji: str) -> None:
        if self.message_id:
            await self.ws.unreact(self.message_id, emoji)
    
    async def typing(self) -> None:
        await self.ws.start_typing(self.channel_id)
