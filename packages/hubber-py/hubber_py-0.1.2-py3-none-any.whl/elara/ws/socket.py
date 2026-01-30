import socketio
from typing import Callable, Dict, Any, Optional, TYPE_CHECKING
from ..utils.ratelimit import RateLimiter

if TYPE_CHECKING:
    from ..cache import Cache


class WebSocketClient:
    def __init__(self, enable_ratelimit: bool = True, cache: Optional['Cache'] = None):
        self.sio = socketio.AsyncClient()
        self._handlers: Dict[str, Callable] = {}
        self._setup_internal_handlers()
        self.enable_ratelimit = enable_ratelimit
        self.cache = cache
        if enable_ratelimit:
            self._message_limiter = RateLimiter(5, 5.0)
            self._channel_limiter = RateLimiter(2, 5.0)
    
    def _setup_internal_handlers(self):
        events = [
            "connect", "ready", "message:new", "message:edit", "message:delete",
            "message:reaction_add", "message:reaction_remove", "server:member_join",
            "server:member_leave", "typing:start", "presence:update",
            "interaction:button", "session:expired"
        ]
        
        for event in events:
            @self.sio.on(event)
            async def _handler(data=None, evt=event):
                if evt in self._handlers:
                    if data is not None:
                        await self._handlers[evt](data)
                    else:
                        await self._handlers[evt]()
    
    def on(self, event: str):
        def decorator(func: Callable):
            self._handlers[event] = func
            return func
        return decorator
    
    async def connect(self, socket_token: str):
        await self.sio.connect(
            "https://hubber.cc",
            auth={"token": socket_token},
            transports=["websocket"]
        )
    
    async def emit(self, event: str, data: Dict[str, Any], callback: Optional[Callable] = None):
        if callback:
            await self.sio.emit(event, data, callback=callback)
        else:
            await self.sio.emit(event, data)
    
    async def send_message(self, channel_id: str, content: str = None, embeds: list = None, components: list = None, reply_to: str = None):
        if self.cache:
            cache_key = f"ratelimit:message:{channel_id}"
            cached = await self.cache.get(cache_key)
            if cached and self.enable_ratelimit:
                wait_time = self._message_limiter.get_wait_time()
                if wait_time > 0:
                    await self.cache.set(cache_key, True, ttl=wait_time)
        
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        
        data = {"channelId": channel_id}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if components:
            data["components"] = components
        if reply_to:
            data["replyTo"] = reply_to
        await self.emit("message:send", data)
        
        if self.cache:
            await self.cache.set(f"ratelimit:message:{channel_id}", True, ttl=1.0)
    
    async def start_typing(self, channel_id: str):
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        await self.emit("typing:start", {"channelId": channel_id})
    
    async def react(self, message_id: str, emoji: str):
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        await self.emit("message:react", {"messageId": message_id, "emoji": emoji})
    
    async def unreact(self, message_id: str, emoji: str):
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        await self.emit("message:unreact", {"messageId": message_id, "emoji": emoji})
    
    async def edit_message(self, message_id: str, content: str):
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        await self.emit("message:edit", {"messageId": message_id, "content": content})
    
    async def delete_message(self, message_id: str):
        if self.enable_ratelimit:
            await self._message_limiter.acquire()
        await self.emit("message:delete", {"messageId": message_id})
    
    async def create_channel(self, server_id: str, name: str, channel_type: str = "text"):
        if self.enable_ratelimit:
            await self._channel_limiter.acquire()
        await self.emit("channel:create", {"serverId": server_id, "name": name, "type": channel_type})
    
    async def delete_channel(self, channel_id: str):
        if self.enable_ratelimit:
            await self._channel_limiter.acquire()
        await self.emit("channel:delete", {"channelId": channel_id})
    
    async def add_role(self, server_id: str, user_id: str, role_id: str):
        await self.emit("role:add", {"serverId": server_id, "userId": user_id, "roleId": role_id})
    
    async def remove_role(self, server_id: str, user_id: str, role_id: str):
        await self.emit("role:remove", {"serverId": server_id, "userId": user_id, "roleId": role_id})
    
    async def reply_interaction(self, interaction_id: str, content: str, ephemeral: bool = False):
        data = {"interactionId": interaction_id, "content": content, "ephemeral": ephemeral}
        await self.emit("interaction:reply", data)
    
    async def disconnect(self):
        await self.sio.disconnect()
    
    async def wait(self):
        await self.sio.wait()
