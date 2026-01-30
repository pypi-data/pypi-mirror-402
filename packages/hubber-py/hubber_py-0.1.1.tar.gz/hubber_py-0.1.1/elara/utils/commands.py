from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Command:
    name: str
    callback: Callable
    description: Optional[str] = None
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class CommandHandler:
    def __init__(self, prefix: str = "!"):
        self.prefix = prefix
        self.commands: Dict[str, Command] = {}
    
    def command(self, name: Optional[str] = None, description: Optional[str] = None, aliases: Optional[List[str]] = None):
        def decorator(func: Callable):
            cmd_name = name or func.__name__
            cmd = Command(cmd_name, func, description, aliases or [])
            self.commands[cmd_name] = cmd
            for alias in cmd.aliases:
                self.commands[alias] = cmd
            return func
        return decorator
    
    async def process_message(self, ctx: Any) -> bool:
        content = ctx.content.strip()
        if not content.startswith(self.prefix):
            return False
        
        parts = content[len(self.prefix):].split(maxsplit=1)
        if not parts:
            return False
        
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        command = self.commands.get(cmd_name)
        if not command:
            return False
        
        ctx.args = args
        ctx.command = command
        await command.callback(ctx)
        return True
    
    def get_command(self, name: str) -> Optional[Command]:
        return self.commands.get(name)
    
    def remove_command(self, name: str) -> bool:
        if name in self.commands:
            del self.commands[name]
            return True
        return False
