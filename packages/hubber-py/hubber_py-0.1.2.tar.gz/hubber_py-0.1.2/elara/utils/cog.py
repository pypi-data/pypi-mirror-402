from typing import TYPE_CHECKING, Optional, List, Dict, Any, Callable

if TYPE_CHECKING:
    from ..main import Client


class Cog:
    def __init__(self, client: 'Client'):
        self.client = client
        self._commands: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        
        for name in dir(self):
            func = getattr(self, name)
            if hasattr(func, '__cog_command__'):
                self._commands[func.__cog_command__['name']] = func
            if hasattr(func, '__cog_listener__'):
                event = func.__cog_listener__
                self._listeners.setdefault(event, []).append(func)
    
    @staticmethod
    def command(name: Optional[str] = None, description: Optional[str] = None, aliases: Optional[List[str]] = None):
        def decorator(func):
            func.__cog_command__ = {
                'name': name or func.__name__,
                'description': description,
                'aliases': aliases or []
            }
            return func
        return decorator
    
    @staticmethod
    def listener(event: str):
        def decorator(func):
            func.__cog_listener__ = event
            return func
        return decorator
    
    def _inject(self, client: 'Client') -> None:
        for name, func in self._commands.items():
            cmd_info = func.__cog_command__
            client.command_handler.command(
                name=cmd_info['name'],
                description=cmd_info['description'],
                aliases=cmd_info['aliases']
            )(func)
        for event, listeners in self._listeners.items():
            for listener in listeners:
                client._event_listeners.setdefault(event, []).append(listener)
    
    def _eject(self, client: 'Client') -> None:
        for name in self._commands:
            client.command_handler.commands.pop(name, None)
        for event, listeners in self._listeners.items():
            if event in client._event_listeners:
                for listener in listeners:
                    if listener in client._event_listeners[event]:
                        client._event_listeners[event].remove(listener)
    
    async def cog_load(self) -> None:
        pass
    
    async def cog_unload(self) -> None:
        pass
