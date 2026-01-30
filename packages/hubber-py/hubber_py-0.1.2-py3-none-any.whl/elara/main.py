from .ws import Auth, WebSocketClient
from .context import Context, Interaction, Reaction
from .utils import CommandHandler
from .utils.cogmanager import CogManager
from .cache import Cache
from typing import Optional, Callable, List, Dict
import asyncio


class Client:
    def __init__(self, token: str, prefix: str = "!", enable_ratelimit: bool = True, enable_cache: bool = True):
        self.auth = Auth(token)
        self.cache = Cache(max_size=10000, default_ttl=300.0) if enable_cache else None
        self.ws = WebSocketClient(enable_ratelimit, self.cache)
        self._socket_token: Optional[str] = None
        self.user = None
        self.command_handler = CommandHandler(prefix)
        self._setup_command_processor()
        self._reconnect_attempts = 0
        self.cogs = CogManager(self)
        self._event_listeners: Dict[str, List[Callable]] = {}
    
    def _setup_command_processor(self):
        @self.on("message:new")
        async def _process_commands(ctx):
            await self.command_handler.process_message(ctx)
    
    def command(self, name: Optional[str] = None, description: Optional[str] = None, aliases: Optional[List[str]] = None):
        return self.command_handler.command(name, description, aliases)
    
    def on(self, event: str):
        def decorator(func: Callable):
            if event == "message:new":
                async def wrapper(data):
                    ctx = Context(self.ws, data)
                    await func(ctx)
                    for listener in self._event_listeners.get(event, []):
                        await listener(ctx)
                self.ws._handlers[event] = wrapper
                return func
            elif event == "interaction:button":
                async def wrapper(data):
                    ctx = Interaction(self.ws, data)
                    await func(ctx)
                    for listener in self._event_listeners.get(event, []):
                        await listener(ctx)
                self.ws._handlers[event] = wrapper
                return func
            else:
                async def wrapper(*args, **kwargs):
                    await func(*args, **kwargs)
                    for listener in self._event_listeners.get(event, []):
                        await listener(*args, **kwargs)
                self.ws._handlers[event] = wrapper
                return func
        return decorator
    
    def _setup_event_wrappers(self):
        if "message:new" not in self.ws._handlers:
            async def message_wrapper(data):
                ctx = Context(self.ws, data)
                for listener in self._event_listeners.get("message:new", []):
                    await listener(ctx)
            self.ws._handlers["message:new"] = message_wrapper
        
        if "interaction:button" not in self.ws._handlers:
            async def button_wrapper(data):
                ctx = Interaction(self.ws, data)
                for listener in self._event_listeners.get("interaction:button", []):
                    await listener(ctx)
            self.ws._handlers["interaction:button"] = button_wrapper
        
        if "message:reaction_add" not in self.ws._handlers:
            async def reaction_add_wrapper(data):
                ctx = Reaction(self.ws, data)
                for listener in self._event_listeners.get("message:reaction_add", []):
                    await listener(ctx)
            self.ws._handlers["message:reaction_add"] = reaction_add_wrapper
        
        if "message:reaction_remove" not in self.ws._handlers:
            async def reaction_remove_wrapper(data):
                ctx = Reaction(self.ws, data)
                for listener in self._event_listeners.get("message:reaction_remove", []):
                    await listener(ctx)
            self.ws._handlers["message:reaction_remove"] = reaction_remove_wrapper
    
    async def load_cog(self, path: str) -> None:
        await self.cogs.load(path)
    
    async def unload_cog(self, cog_name: str) -> None:
        await self.cogs.unload(cog_name)
    
    async def reload_cog(self, cog_name: str) -> None:
        await self.cogs.reload(cog_name)
    
    async def add_cog(self, cog) -> None:
        cog._inject(self)
        await cog.cog_load()
        cog_name = cog.__class__.__name__
        self.cogs._cogs[cog_name] = cog
        self._setup_event_wrappers()
    
    async def send_message(self, channel_id: str, content: str):
        await self.ws.send_message(channel_id, content)
    
    async def connect(self):
        self._socket_token = await self.auth.get_socket_token()
        await self.ws.connect(self._socket_token)
        self._reconnect_attempts = 0
    
    async def disconnect(self):
        await self.ws.disconnect()
        await self.auth.close()
        if self.cache:
            await self.cache.close()
    
    async def _reconnect(self):
        while True:
            delays = [5, 10, 30, 60, 120, 300]
            delay = delays[min(self._reconnect_attempts, len(delays) - 1)]
            print(f"Reconnecting in {delay}s... (attempt {self._reconnect_attempts + 1})")
            await asyncio.sleep(delay)
            self._reconnect_attempts += 1
            try:
                await self.connect()
                break
            except Exception as e:
                print(f"Reconnection failed: {e}")
    
    async def run(self):
        while True:
            try:
                await self.connect()
                self._reconnect_attempts = 0
                await self.ws.wait()
            except Exception as e:
                print(f"Connection lost: {e}")
                await self._reconnect()
